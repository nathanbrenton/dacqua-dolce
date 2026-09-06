import {
  useEffect,
  useState,
} from "react";

import {
  getCurrentAccount,
  logoutAccount,
  type AuthenticationStatus,
} from "./api/authentication";
import { getBackendHealth } from "./api/backend";
import { AuthDialog } from "./components/auth/AuthDialog";
import { BrandLogo } from "./components/brand/BrandLogo";
import { CatalogSection } from "./components/catalog/CatalogSection";
import { ProductDetailPage } from "./components/catalog/ProductDetailPage";
import { DeveloperControls } from "./components/developer/DeveloperControls";
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
  "dacqua-dolce-theme";

const LOGO_STORAGE_KEY =
  "dacqua-dolce-logo";

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

export function App() {
  const [backendState, setBackendState] =
    useState<BackendState>("checking");

  const [theme, setTheme] =
    useState<ThemeId>(getInitialTheme);

  const [logoVariant, setLogoVariant] =
    useState<LogoVariantId>(
      getInitialLogo,
    );

  const [account, setAccount] =
    useState<AuthenticationStatus | null>(
      null,
    );

  const [accountReady, setAccountReady] =
    useState(false);

  const [
    authDialogOpen,
    setAuthDialogOpen,
  ] = useState(false);

  const [path, setPath] = useState(
    window.location.pathname,
  );

  useEffect(() => {
    document.documentElement.dataset.theme =
      theme;

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
        setBackendState("online");
      })
      .catch(() => {
        setBackendState("offline");
      });
  }, []);

  useEffect(() => {
    void getCurrentAccount()
      .then((currentAccount) => {
        setAccount(currentAccount);
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

  function navigate(nextPath: string) {
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
    }
  }

  const detailMatch = path.match(
    /^\/systems\/([^/]+)\/?$/,
  );

  const detailSlug =
    detailMatch?.[1] ?? null;

  return (
    <>
      <DeveloperControls
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
          setAuthDialogOpen(false);
        }}
        onAuthenticated={(
          authenticatedAccount,
        ) => {
          setAccount(
            authenticatedAccount,
          );
          setAccountReady(true);
        }}
      />

      {detailSlug !== null ? (
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
      ) : (
        <main className="site-shell">
          <header className="site-header">
            <button
              type="button"
              className="brand-logo-link"
              aria-label="D'Acqua Dolce home"
              onClick={() => {
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

            <nav aria-label="Primary navigation">
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
              Thoughtfully engineered water
              filtration for the home,
              supported throughout the life
              of the system.
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
              >
                Talk to an Expert
              </button>
            </div>
          </section>

          <CatalogSection
            onNavigate={navigate}
          />

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
                className={`status-dot status-${backendState}`}
                aria-hidden="true"
              />

              Local API: {backendState}
            </div>
          </footer>
        </main>
      )}
    </>
  );
}
