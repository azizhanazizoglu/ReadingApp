import { useState, useCallback } from 'react';

export interface ActionData {
	id: string;
	type: 'click' | 'input' | 'wait' | 'custom';
	selector: string;
	value?: string;
	waitMs?: number;
	description?: string;
}

export interface ActionsManagerOptions {
	logInfo: (msg: string) => void;
	logWarn: (msg: string) => void;
	logError: (msg: string) => void;
}

export const useActionsManager = (options: ActionsManagerOptions) => {
	const { logInfo, logWarn, logError } = options;
	
	const [actions, setActions] = useState<ActionData[]>([]);

	const addAction = useCallback((type: ActionData['type']) => {
		const newAction: ActionData = {
			id: `action_${Date.now().toString(36)}`,
			type,
			selector: '',
			description: `${type.charAt(0).toUpperCase() + type.slice(1)} action`
		};
		
		setActions(prev => [...prev, newAction]);
		logInfo(`Action added: ${newAction.description}`);
		return newAction.id;
	}, [logInfo]);

	const updateAction = useCallback((id: string, updates: Partial<ActionData>) => {
		setActions(prev => prev.map(action => 
			action.id === id ? { ...action, ...updates } : action
		));
		logInfo(`Action updated: ${id}`);
	}, [logInfo]);

	const removeAction = useCallback((id: string) => {
		const action = actions.find(a => a.id === id);
		setActions(prev => prev.filter(action => action.id !== id));
		logInfo(`Action removed: ${action?.description || id}`);
	}, [actions, logInfo]);

	const moveAction = useCallback((id: string, direction: 'up' | 'down') => {
		setActions(prev => {
			const index = prev.findIndex(a => a.id === id);
			if (index === -1) return prev;
			
			const newIndex = direction === 'up' ? index - 1 : index + 1;
			if (newIndex < 0 || newIndex >= prev.length) return prev;
			
			const newActions = [...prev];
			[newActions[index], newActions[newIndex]] = [newActions[newIndex], newActions[index]];
			
			logInfo(`Action moved ${direction}: ${prev[index].description}`);
			return newActions;
		});
	}, [logInfo]);

	const duplicateAction = useCallback((id: string) => {
		const action = actions.find(a => a.id === id);
		if (!action) {
			logWarn(`Action not found for duplication: ${id}`);
			return;
		}
		
		const duplicated: ActionData = {
			...action,
			id: `action_${Date.now().toString(36)}`,
			description: `${action.description} (copy)`
		};
		
		setActions(prev => {
			const index = prev.findIndex(a => a.id === id);
			const newActions = [...prev];
			newActions.splice(index + 1, 0, duplicated);
			return newActions;
		});
		
		logInfo(`Action duplicated: ${duplicated.description}`);
		return duplicated.id;
	}, [actions, logInfo, logWarn]);

	const clearAllActions = useCallback(() => {
		setActions([]);
		logInfo('All actions cleared');
	}, [logInfo]);

	const validateActions = useCallback(() => {
		const issues: string[] = [];
		
		actions.forEach((action, index) => {
			if (!action.selector && action.type !== 'wait') {
				issues.push(`Action ${index + 1}: Missing selector`);
			}
			if (action.type === 'input' && !action.value) {
				issues.push(`Action ${index + 1}: Input action missing value`);
			}
			if (action.type === 'wait' && (!action.waitMs || action.waitMs <= 0)) {
				issues.push(`Action ${index + 1}: Wait action missing or invalid duration`);
			}
		});

		if (issues.length > 0) {
			logWarn(`Action validation issues: ${issues.join(', ')}`);
		} else {
			logInfo('All actions validated successfully');
		}

		return issues;
	}, [actions, logInfo, logWarn]);

	const getActionById = useCallback((id: string) => {
		return actions.find(a => a.id === id);
	}, [actions]);

	return {
		// State
		actions,
		
		// Setters
		setActions,
		
		// Operations
		addAction,
		updateAction,
		removeAction,
		moveAction,
		duplicateAction,
		clearAllActions,
		validateActions,
		getActionById,
	};
};