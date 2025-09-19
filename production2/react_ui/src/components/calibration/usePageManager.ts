import { useState, useCallback } from 'react';

export interface PageData {
	id: string;
	name: string;
	url: string;
	fieldSelectors: Record<string, string | string[]>;
}

export interface PageManagerOptions {
	logInfo: (msg: string) => void;
	logWarn: (msg: string) => void;
	logError: (msg: string) => void;
}

export const usePageManager = (options: PageManagerOptions) => {
	const { logInfo, logWarn, logError } = options;
	
	const [pages, setPages] = useState<PageData[]>([{
		id: `p_${Date.now().toString(36)}`,
		name: 'Page 1',
		url: '',
		fieldSelectors: {}
	}]);
	
	const [currentPageId, setCurrentPageId] = useState<string>(() => `p_${Date.now().toString(36)}`);

	const syncFieldSelectorsToPage = useCallback((next: Record<string, string | string[]>) => {
		setPages(prev => prev.map(p => p.id === currentPageId ? { ...p, fieldSelectors: next } : p));
	}, [currentPageId]);

	const addPage = useCallback(async () => {
		try {
			const newPageId = `p_${Date.now().toString(36)}`;
			const newPage: PageData = {
				id: newPageId,
				name: `Page ${pages.length + 1}`,
				url: '',
				fieldSelectors: {}
			};
			
			setPages(prev => [...prev, newPage]);
			setCurrentPageId(newPageId);
			logInfo(`New page added: ${newPage.name}`);
		} catch (e) {
			logError(`Failed to add new page: ${e}`);
		}
	}, [pages.length, logInfo, logError]);

	const deletePage = useCallback(async (pageId: string) => {
		if (pages.length <= 1) {
			logWarn('Cannot delete the last page');
			return;
		}

		try {
			const pageToDelete = pages.find(p => p.id === pageId);
			if (!pageToDelete) {
				logWarn('Page not found for deletion');
				return;
			}

			setPages(prev => prev.filter(p => p.id !== pageId));
			
			// Switch to another page if current page was deleted
			if (currentPageId === pageId) {
				const remainingPages = pages.filter(p => p.id !== pageId);
				if (remainingPages.length > 0) {
					setCurrentPageId(remainingPages[0].id);
				}
			}
			
			logInfo(`Page deleted: ${pageToDelete.name}`);
		} catch (e) {
			logError(`Failed to delete page: ${e}`);
		}
	}, [pages, currentPageId, logInfo, logWarn, logError]);

	const updatePageName = useCallback((pageId: string, newName: string) => {
		setPages(prev => prev.map(p => 
			p.id === pageId ? { ...p, name: newName } : p
		));
		logInfo(`Page renamed to: ${newName}`);
	}, [logInfo]);

	const updatePageUrl = useCallback((pageId: string, newUrl: string) => {
		setPages(prev => prev.map(p => 
			p.id === pageId ? { ...p, url: newUrl } : p
		));
		logInfo(`Page URL updated: ${newUrl}`);
	}, [logInfo]);

	const getCurrentPage = useCallback(() => {
		return pages.find(p => p.id === currentPageId) || pages[0];
	}, [pages, currentPageId]);

	const switchToPage = useCallback((pageId: string) => {
		const page = pages.find(p => p.id === pageId);
		if (page) {
			setCurrentPageId(pageId);
			logInfo(`Switched to page: ${page.name}`);
			return page;
		}
		logWarn(`Page not found: ${pageId}`);
		return null;
	}, [pages, logInfo, logWarn]);

	return {
		// State
		pages,
		currentPageId,
		
		// Setters
		setPages,
		setCurrentPageId,
		
		// Operations
		addPage,
		deletePage,
		updatePageName,
		updatePageUrl,
		switchToPage,
		getCurrentPage,
		syncFieldSelectorsToPage,
	};
};