// Toaster removed. Provide no-op helpers to keep call sites safe.
export const showSuccess = (message: string) => {
  if (import.meta.env.DEV) console.info("SUCCESS:", message);
};

export const showError = (message: string) => {
  if (import.meta.env.DEV) console.error("ERROR:", message);
};

export const showLoading = (message: string) => {
  if (import.meta.env.DEV) console.info("LOADING:", message);
  return undefined as unknown as string;
};

export const dismissToast = (_toastId: string) => {
  // no-op
};
