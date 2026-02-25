// SPDX-License-Identifier: MIT

/**
 * Turnstile Verification Middleware
 * Cloudflare Turnstile challenge validation for bot protection
 *
 * @see https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
 */

import type { Env, TurnstileResult } from '../types';
import { CONFIG } from '../config';

interface SiteverifyResponse {
	success: boolean;
	'error-codes': string[];
	challenge_ts?: string;
	hostname?: string;
}

function getClientIP(request: Request): string {
	return request.headers.get('CF-Connecting-IP') || 'unknown';
}

async function verifySiteverify(
	token: string,
	ip: string,
	secretKey: string,
): Promise<{ success: boolean; errors: string[] }> {
	const response = await fetch(CONFIG.turnstile.siteverifyUrl, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			secret: secretKey,
			response: token,
			remoteip: ip,
		}),
	});

	if (!response.ok) {
		return { success: false, errors: [`siteverify returned ${response.status}`] };
	}

	const data = (await response.json()) as SiteverifyResponse;
	return { success: data.success, errors: data['error-codes'] || [] };
}

/**
 * Check Turnstile verification token.
 * Skipped in development mode or when TURNSTILE_SECRET_KEY is not set.
 */
export async function checkTurnstile(request: Request, env: Env): Promise<TurnstileResult> {
	if (env.ENVIRONMENT === 'development') {
		return { allowed: true };
	}

	if (!env.TURNSTILE_SECRET_KEY) {
		return { allowed: true };
	}

	const token = request.headers.get('X-Turnstile-Token');
	if (!token) {
		return { allowed: false, error: 'missing_token' };
	}

	const ip = getClientIP(request);
	const result = await verifySiteverify(token, ip, env.TURNSTILE_SECRET_KEY);

	if (!result.success) {
		return { allowed: false, error: 'invalid_token' };
	}

	return { allowed: true };
}
