// SPDX-License-Identifier: MIT

/**
 * Rate Limiting Middleware
 * KV-based rate limiting for API protection
 */

import type { Env, RateLimitResult } from '../types';
import { CONFIG } from '../config';

function getClientIP(request: Request): string {
	return request.headers.get('CF-Connecting-IP') || 'unknown';
}

async function checkWindow(
	kv: KVNamespace,
	key: string,
	limit: number,
	ttl: number,
): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
	const value = await kv.get(key);
	const count = value ? parseInt(value) : 0;
	const now = Date.now();

	if (count >= limit) {
		return { allowed: false, remaining: 0, resetAt: now + ttl * 1000 };
	}

	await kv.put(key, String(count + 1), { expirationTtl: ttl });

	return { allowed: true, remaining: limit - count - 1, resetAt: now + ttl * 1000 };
}

async function checkMinuteRateLimit(request: Request, env: Env): Promise<RateLimitResult> {
	if (env.ENVIRONMENT === 'development') {
		return { allowed: true, remaining: CONFIG.rateLimit.requestsPerMinute, resetAt: Date.now() + 60000 };
	}

	const ip = getClientIP(request);
	const result = await checkWindow(env.EU_AI_ACT_RAG_WORKER_KV, `ratelimit:minute:${ip}`, CONFIG.rateLimit.requestsPerMinute, 60);

	return {
		...result,
		retryAfter: result.allowed ? undefined : Math.ceil((result.resetAt - Date.now()) / 1000),
	};
}

async function checkHourRateLimit(request: Request, env: Env): Promise<RateLimitResult> {
	if (env.ENVIRONMENT === 'development') {
		return { allowed: true, remaining: CONFIG.rateLimit.requestsPerHour, resetAt: Date.now() + 3600000 };
	}

	const ip = getClientIP(request);
	const result = await checkWindow(env.EU_AI_ACT_RAG_WORKER_KV, `ratelimit:hour:${ip}`, CONFIG.rateLimit.requestsPerHour, 3600);

	return {
		...result,
		retryAfter: result.allowed ? undefined : Math.ceil((result.resetAt - Date.now()) / 1000),
	};
}

async function checkDayRateLimit(request: Request, env: Env): Promise<RateLimitResult> {
	if (env.ENVIRONMENT === 'development') {
		return { allowed: true, remaining: CONFIG.rateLimit.requestsPerDay, resetAt: Date.now() + 86400000 };
	}

	const ip = getClientIP(request);
	const result = await checkWindow(env.EU_AI_ACT_RAG_WORKER_KV, `ratelimit:day:${ip}`, CONFIG.rateLimit.requestsPerDay, 86400);

	return {
		...result,
		retryAfter: result.allowed ? undefined : Math.ceil((result.resetAt - Date.now()) / 1000),
	};
}

/**
 * Check all rate limits (minute, hour, day)
 * Returns first limit that is exceeded
 */
export async function checkRateLimits(request: Request, env: Env): Promise<RateLimitResult> {
	const minuteResult = await checkMinuteRateLimit(request, env);
	if (!minuteResult.allowed) return minuteResult;

	const hourResult = await checkHourRateLimit(request, env);
	if (!hourResult.allowed) return hourResult;

	const dayResult = await checkDayRateLimit(request, env);
	if (!dayResult.allowed) return dayResult;

	return minuteResult;
}
