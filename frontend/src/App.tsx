import {
  useEffect,
  useState,
} from "react";

import {
  getCurrentAccount,
  logoutAccount,
  type AuthenticationStatus,
} from "./api/authentication";
import {
  getBackendHealth,
} from "./api/backend";
import {
  AccountPage,
} from "./components/account/AccountPage";
import {
  AuthDialog,
} from "./components/auth/AuthDialog";
import {
  BrandLogo,
} from "./components/brand/BrandLogo";
import {
  CatalogSection,
} from "./components/catalog/CatalogSection";
import {
  ProductDetailPage,
} from "./components/catalog/ProductDetailPage";
import {
  DeveloperControls,
} from "./components/developer/DeveloperControls";
import {
  OperationsPage,
} from "./components/operations/OperationsPage";
import {
  QuoteDialog,
} from "./components/quotes/QuoteDialog";
import {
  ForgotPasswordPage,
} from "./pages/ForgotPasswordPage";
import {
  ResetPasswordPage,
} from "./pages/ResetPasswordPage";
import {
  DEFAULT_LOGO_VARIANT,
  isLogoVariantId,
  type LogoVariantId,
} from "./theme/branding";
import {
  DEFAULT_THEME,
  isThemeId,
  type ThemeId,
} from "./theme/themes";

type BackendState =
  | "checking"
  | "online"
  | "offline";

const THEME_STORAGE_KEY =
  "dacqua-dolce-theme-v2";

const LOGO_STORAGE_KEY =
  "dacqua-dolce-logo-v2";

function getInitialTheme(): ThemeId {
  const storedTheme =
    localStorage.getItem(
      THEME_STORAGE_KEY,
    );

  if (
    storedTheme !== null
    && isThemeId(storedTheme)
  ) {
    return storedTheme;
  }

  return DEFAULT_THEME;
}

function getInitialLogo(): LogoVariantId {
  const storedLogo =
    localStorage.getItem(
      LOGO_STORAGE_KEY,
    );

  if (
    storedLogo !== null
    && isLogoVariantId(storedLogo)
  ) {
    return storedLogo;
  }

  return DEFAULT_LOGO_VARIANT;
}


const OPERATIONS_ROLE_NAMES = new Set([
  "employee",
  "manager",
  "administrator",
  "developer",
]);

function hasOperationsRole(
  account: AuthenticationStatus | null,
): boolean {
  return (
    account?.roles.some((role) =>
      OPERATIONS_ROLE_NAMES.has(role),
    ) ?? false
  );
}

export function App() {
  const [
    backendState,
    setBackendState,
  ] = useState<BackendState>(
    "checking",
  );

  const [theme, setTheme] =
    useState<ThemeId>(
      getInitialTheme,
    );

  const [
    logoVariant,
    setLogoVariant,
  ] = useState<LogoVariantId>(
    getInitialLogo,
  );

  const [account, setAccount] =
    useState<
      AuthenticationStatus | null
    >(null);

  const [
    accountReady,
    setAccountReady,
  ] = useState(false);

  const [
    authDialogOpen,
    setAuthDialogOpen,
  ] = useState(false);

  const [
    generalQuoteOpen,
    setGeneralQuoteOpen,
  ] = useState(false);

  const [
    developerControlsOpen,
    setDeveloperControlsOpen,
  ] = useState(false);

  const developerMode =
    import.meta.env.VITE_DEVELOPER_MODE
    === "true";

  const [path, setPath] =
    useState(
      window.location.pathname,
    );

  useEffect(() => {
    document.documentElement
      .dataset.theme = theme;

    localStorage.setItem(
      THEME_STORAGE_KEY,
      theme,
    );
  }, [theme]);

  useEffect(() => {
    localStorage.setItem(
      LOGO_STORAGE_KEY,
      logoVariant,
    );
  }, [logoVariant]);

  useEffect(() => {
    void getBackendHealth()
      .then(() => {
        setBackendState(
          "online",
        );
      })
      .catch(() => {
        setBackendState(
          "offline",
        );
      });
  }, []);

  useEffect(() => {
    void getCurrentAccount()
      .then((currentAccount) => {
        setAccount(
          currentAccount,
        );
      })
      .catch(() => {
        setAccount(null);
      })
      .finally(() => {
        setAccountReady(true);
      });
  }, []);

  useEffect(() => {
    function handlePopState() {
      setPath(
        window.location.pathname,
      );
    }

    window.addEventListener(
      "popstate",
      handlePopState,
    );

    return () => {
      window.removeEventListener(
        "popstate",
        handlePopState,
      );
    };
  }, []);

  function navigate(
    nextPath: string,
  ) {
    if (
      window.location.pathname
      !== nextPath
    ) {
      window.history.pushState(
        {},
        "",
        nextPath,
      );
    }

    setPath(nextPath);
    setDeveloperControlsOpen(false);

    window.scrollTo({
      top: 0,
      behavior: "instant",
    });
  }

  async function signOut() {
    try {
      await logoutAccount();
    } finally {
      setAccount(null);
      navigate("/");
    }
  }

  const detailMatch = path.match(
    /^\/systems\/([^/]+)\/?$/,
  );

  const detailSlug =
    detailMatch?.[1] ?? null;

  const resetMatch = path.match(
    /^\/reset-password\/([^/]+)\/?$/,
  );

  const resetToken =
    resetMatch?.[1] ?? null;

  const isHome =
    path === "/" || path === "";

  return (
    <>
      <DeveloperControls
        open={developerControlsOpen}
        theme={theme}
        onThemeChange={setTheme}
        logoVariant={logoVariant}
        onLogoVariantChange={
          setLogoVariant
        }
      />

      <AuthDialog
        open={authDialogOpen}
        onClose={() => {
          setAuthDialogOpen(
            false,
          );
        }}
        onAuthenticated={(
          authenticatedAccount,
        ) => {
          setAccount(
            authenticatedAccount,
          );
          setAccountReady(true);
        }}
        onForgotPassword={() => {
          navigate(
            "/forgot-password",
          );
        }}
      />

      <QuoteDialog
        open={generalQuoteOpen}
        productId={null}
        productName={
          "Talk to an Expert"
        }
        initialEmail={
          account?.email ?? null
        }
        onClose={() => {
          setGeneralQuoteOpen(
            false,
          );
        }}
      />

      {path === "/operations" ? (
        <OperationsPage
          roles={account?.roles ?? []}
          onNavigate={navigate}
        />
      ) : path === "/account" ? (
        <AccountPage
          authenticated={
            account !== null
          }
          onNavigate={navigate}
          onRequestSignIn={() => {
            setAuthDialogOpen(true);
          }}
        />
      ) : path
        === "/forgot-password" ? (
        <ForgotPasswordPage
          onNavigate={navigate}
        />
      ) : resetToken
        !== null ? (
        <ResetPasswordPage
          token={decodeURIComponent(
            resetToken,
          )}
          onNavigate={navigate}
          onResetComplete={() => {
            setAccount(null);
            setAccountReady(true);
            setAuthDialogOpen(true);
          }}
        />
      ) : detailSlug
        !== null ? (
        <ProductDetailPage
          slug={decodeURIComponent(
            detailSlug,
          )}
          account={account}
          onNavigate={navigate}
          onRequestSignIn={() => {
            setAuthDialogOpen(true);
          }}
        />
      ) : isHome ? (
        <main className="site-shell">
          <header className="site-header">
            <button
              type="button"
              className="brand-logo-link"
              aria-label={
                developerMode
                  ? "Toggle developer visual controls"
                  : "D'Acqua Dolce home"
              }
              aria-expanded={
                developerMode
                  ? developerControlsOpen
                  : undefined
              }
              onClick={() => {
                if (developerMode) {
                  setDeveloperControlsOpen(
                    (current) => !current,
                  );
                  return;
                }

                navigate("/");
              }}
            >
              <span className="brand-logo-frame">
                <BrandLogo
                  variant={
                    logoVariant
                  }
                  className="brand-logo"
                />
              </span>
            </button>

            <nav
              aria-label="Primary navigation"
            >
              <a href="#systems">
                Systems
              </a>

              <a href="#service">
                Service
              </a>

              <a href="#about">
                About
              </a>

              {!accountReady ? (
                <button
                  type="button"
                  disabled
                >
                  Checking...
                </button>
              ) : account === null ? (
                <button
                  type="button"
                  onClick={() => {
                    setAuthDialogOpen(
                      true,
                    );
                  }}
                >
                  Sign In
                </button>
              ) : (
                <div className="account-controls">
                  <span
                    className="account-email"
                    title={
                      account.email
                      ?? undefined
                    }
                  >
                    {account.email}
                  </span>

                  {hasOperationsRole(
                    account,
                  ) ? (
                    <button
                      type="button"
                      onClick={() => {
                        navigate(
                          "/operations",
                        );
                      }}
                    >
                      Operations
                    </button>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => {
                      navigate(
                        "/account",
                      );
                    }}
                  >
                    Account
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      void signOut();
                    }}
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </nav>
          </header>

          <section className="hero">
            <p className="eyebrow">
              Premium Water Filtration
            </p>

            <h1>
              Water,
              <br />
              Elevated.
            </h1>

            <p className="hero-copy">
              Thoughtfully engineered
              water filtration for the
              home, supported throughout
              the life of the system.
            </p>

            <div className="hero-actions">
              <a
                className="primary-button"
                href="#systems"
              >
                Explore Systems
              </a>

              <button
                className="secondary"
                type="button"
                onClick={() => {
                  setGeneralQuoteOpen(
                    true,
                  );
                }}
              >
                Talk to an Expert
              </button>
            </div>
          </section>

          <CatalogSection
            onNavigate={navigate}
          />

          <section
            id="service"
            className="service-statement"
          >
            <p className="eyebrow">
              Service
            </p>

            <h2>
              Support beyond installation.
            </h2>

            <p>
              Customer accounts provide
              the foundation for service,
              maintenance, documents,
              warranty, and equipment
              lifecycle features as those
              workflows come online.
            </p>
          </section>

          <section
            id="about"
            className="brand-statement"
          >
            <p className="eyebrow">
              D&apos;Acqua Dolce
            </p>

            <h2>
              Water is not background.
            </h2>

            <p>
              It is part of the home,
              the kitchen, the ritual,
              and the experience.
            </p>
          </section>

          <footer className="site-footer">
            <div className="footer-brand-frame">
              <BrandLogo
                variant={logoVariant}
                filtrationSystems
                className="footer-logo"
              />
            </div>

            <div className="development-status">
              <span
                className={
                  `status-dot `
                  + `status-${backendState}`
                }
                aria-hidden="true"
              />

              Local API: {backendState}
            </div>
          </footer>
        </main>
      ) : (
        <main className="detail-shell">
          <button
            type="button"
            className="text-button"
            onClick={() => {
              navigate("/");
            }}
          >
            ← Home
          </button>

          <h1 className="detail-error-title">
            Page not found.
          </h1>
        </main>
      )}
    </>
  );
}
