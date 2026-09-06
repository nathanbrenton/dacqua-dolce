export type HealthStatus = {
  status: string;
};

export async function getBackendHealth(): Promise<HealthStatus> {
  const response = await fetch("/health");

  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.status}`);
  }

  return response.json() as Promise<HealthStatus>;
}
