/**
 * PDF Download Service
 * 
 * Handles programmatic PDF download capture for TsX static stateflow.
 * When the insurance activation button is clicked, this service captures
 * the generated PDF and saves it to the specified directory.
 */

export interface PdfDownloadConfig {
  targetDir: string;
  timeout?: number;
  log?: (msg: string) => void;
}

export interface PdfDownloadResult {
  ok: boolean;
  path?: string;
  filename?: string;
  error?: string;
}

class PdfDownloadService {
  private isSetup = false;
  private downloadPromise: Promise<PdfDownloadResult> | null = null;
  private downloadResolve: ((result: PdfDownloadResult) => void) | null = null;
  private timeoutId: NodeJS.Timeout | null = null;
  private log: (msg: string) => void = () => {};

  /**
   * Setup PDF download interception
   */
  async setup(config: PdfDownloadConfig): Promise<boolean> {
    try {
      this.log = config.log || (() => {});
      this.log('PDF-CAPTURE: Setting up download handler');

      // Check if we're in Electron environment
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        const result = await (window as any).electronAPI.setupPdfDownload({
          targetDir: config.targetDir,
          timeout: config.timeout || 10000
        });
        
        this.isSetup = result?.ok || false;
        this.log(`PDF-CAPTURE: Setup result: ${JSON.stringify(result)}`);
        return this.isSetup;
      } else {
        // Fallback for non-Electron environment (browser)
        this.log('PDF-CAPTURE: Non-Electron environment, using browser fallback');
        this.isSetup = true;
        return true;
      }
    } catch (error) {
      this.log(`PDF-CAPTURE: Setup failed: ${error}`);
      return false;
    }
  }

  /**
   * Start waiting for PDF download
   */
  startWaiting(timeoutMs: number = 15000): Promise<PdfDownloadResult> {
    if (this.downloadPromise) {
      this.log('PDF-CAPTURE: Already waiting for download');
      return this.downloadPromise;
    }

    this.log(`PDF-CAPTURE: Starting to wait for PDF download (timeout: ${timeoutMs}ms)`);

    this.downloadPromise = new Promise((resolve) => {
      this.downloadResolve = resolve;

      // Setup timeout
      this.timeoutId = setTimeout(() => {
        this.log('PDF-CAPTURE: Timeout waiting for download');
        this.resolveDownload({ ok: false, error: 'timeout' });
      }, timeoutMs);

      // If we're in Electron, use IPC
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        (window as any).electronAPI.waitPdfDownload({ timeoutMs })
          .then((result: PdfDownloadResult) => {
            this.log(`PDF-CAPTURE: Electron download result: ${JSON.stringify(result)}`);
            this.resolveDownload(result);
          })
          .catch((error: any) => {
            this.log(`PDF-CAPTURE: Electron download error: ${error}`);
            this.resolveDownload({ ok: false, error: String(error) });
          });
      } else {
        // Browser fallback - check for download indicators in DOM
        this.startBrowserDownloadDetection(timeoutMs);
      }
    });

    return this.downloadPromise;
  }

  /**
   * Browser fallback: detect download by monitoring DOM changes
   */
  private startBrowserDownloadDetection(timeoutMs: number) {
    const startTime = Date.now();
    const checkInterval = 500;

    const checkForDownload = () => {
      if (Date.now() - startTime > timeoutMs) {
        this.resolveDownload({ ok: false, error: 'browser_timeout' });
        return;
      }

      // Check for download-related elements in DOM
      const downloadLinks = document.querySelectorAll('a[href*=".pdf"], a[download*=".pdf"]');
      const downloadButtons = document.querySelectorAll('button[onclick*="download"], button[onclick*=".pdf"]');
      
      if (downloadLinks.length > 0 || downloadButtons.length > 0) {
        this.log(`PDF-CAPTURE: Browser detected download elements: ${downloadLinks.length} links, ${downloadButtons.length} buttons`);
        this.resolveDownload({ 
          ok: true, 
          path: 'browser_download_detected',
          filename: 'police-download.pdf'
        });
        return;
      }

      // Check for browser download indication (this might vary by browser)
      const downloadIndicators = document.querySelectorAll('.download-progress, [class*="download"]');
      if (downloadIndicators.length > 0) {
        this.log('PDF-CAPTURE: Browser download indicators found');
        this.resolveDownload({ 
          ok: true, 
          path: 'browser_download_in_progress',
          filename: 'police-download.pdf'
        });
        return;
      }

      // Continue checking
      setTimeout(checkForDownload, checkInterval);
    };

    setTimeout(checkForDownload, checkInterval);
  }

  /**
   * Resolve the download promise
   */
  private resolveDownload(result: PdfDownloadResult) {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }

    if (this.downloadResolve) {
      this.downloadResolve(result);
      this.downloadResolve = null;
    }

    this.downloadPromise = null;
  }

  /**
   * Check if PDF was generated (alternative method)
   */
  async checkPdfGenerated(html: string): Promise<boolean> {
    // Check for PDF-related elements in HTML
    const pdfPatterns = [
      /href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']/, // PDF links
      /href=["\'](data:application\/pdf[^"\']+)["\']/, // Data URLs
      /<(?:iframe|embed|object)[^>]+(?:type=["\']application\/pdf["\']|src=["\'][^"\']+\.pdf)/, // Embedded PDFs
      /download.*\.pdf/i, // Download attributes
      /blob:.*\/pdf/i, // Blob URLs for PDFs
    ];

    for (const pattern of pdfPatterns) {
      if (pattern.test(html)) {
        this.log('PDF-CAPTURE: PDF evidence found in HTML');
        return true;
      }
    }

    return false;
  }

  /**
   * Cleanup download handler
   */
  async cleanup(): Promise<void> {
    try {
      this.log('PDF-CAPTURE: Cleaning up download handler');

      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null;
      }

      if (this.downloadResolve) {
        this.downloadResolve({ ok: false, error: 'cleanup' });
        this.downloadResolve = null;
      }

      this.downloadPromise = null;

      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        await (window as any).electronAPI.cleanupPdfDownload();
      }

      this.isSetup = false;
      this.log('PDF-CAPTURE: Cleanup complete');
    } catch (error) {
      this.log(`PDF-CAPTURE: Cleanup failed: ${error}`);
    }
  }

  /**
   * Get current setup status
   */
  isReady(): boolean {
    return this.isSetup;
  }
}

// Export singleton instance
export const pdfDownloadService = new PdfDownloadService();

// Export convenience functions
export async function setupPdfDownloadCapture(config: PdfDownloadConfig): Promise<boolean> {
  return pdfDownloadService.setup(config);
}

export async function waitForPdfDownload(timeoutMs: number = 15000, log?: (msg: string) => void): Promise<PdfDownloadResult> {
  if (log) {
    const originalLog = pdfDownloadService['log'];
    pdfDownloadService['log'] = log;
    const result = await pdfDownloadService.startWaiting(timeoutMs);
    pdfDownloadService['log'] = originalLog;
    return result;
  }
  return pdfDownloadService.startWaiting(timeoutMs);
}

export async function cleanupPdfDownloadCapture(log?: (msg: string) => void): Promise<void> {
  if (log) {
    log('PDF-CAPTURE: Requesting cleanup');
  }
  return pdfDownloadService.cleanup();
}

export async function checkPdfInHtml(html: string, log?: (msg: string) => void): Promise<boolean> {
  if (log) {
    log('PDF-CAPTURE: Checking HTML for PDF evidence');
  }
  return pdfDownloadService.checkPdfGenerated(html);
}