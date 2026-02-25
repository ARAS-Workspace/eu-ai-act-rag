// SPDX-License-Identifier: MIT

/**
 * Logging utilities with environment-aware verbosity
 */

import type { Env } from '../types';

export function logError(message: string, error: unknown, env: Env): void {
	if (env.ENVIRONMENT === 'development') {
		console.error(`[DEV] ${message}`, {
			error,
			stack: (error as Error)?.stack,
		});
	} else {
		console.error(`[PROD] ${message}`, {
			message: (error as Error)?.message || 'Unknown error',
		});
	}
}

export function logInfo(message: string, data?: unknown, env?: Env): void {
	if (!env || env.ENVIRONMENT === 'development') {
		console.log(`[INFO] ${message}`, data || '');
	}
}

export function logWarn(message: string, data?: unknown, env?: Env): void {
	if (!env || env.ENVIRONMENT === 'development') {
		console.warn(`[DEV] ${message}`, data || '');
	} else {
		console.warn(`[PROD] ${message}`);
	}
}
