// SPDX-License-Identifier: MIT
// noinspection JSUnusedGlobalSymbols

/**
 * Error Response Utilities
 */

import type { ErrorResponse } from '../types';

const CORS_HEADERS = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'POST, OPTIONS',
	'Access-Control-Allow-Headers': 'Content-Type',
};

export function createErrorResponse(
	errorType: string,
	status: number,
	message: string,
	details?: unknown,
	retryAfter?: number,
): Response {
	const errorBody: ErrorResponse = {
		error: { type: errorType, message, details },
		status,
	};

	if (retryAfter !== undefined) {
		errorBody.retryAfter = retryAfter;
	}

	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...CORS_HEADERS,
	};

	if (retryAfter !== undefined) {
		headers['Retry-After'] = String(retryAfter);
	}

	return new Response(JSON.stringify(errorBody, null, 2), { status, headers });
}

export function badRequest(message: string, details?: unknown): Response {
	return createErrorResponse('invalid_request', 400, message, details);
}

export function notFound(message = 'Endpoint not found'): Response {
	return createErrorResponse('not_found', 404, message);
}

export function methodNotAllowed(message = 'Method not allowed'): Response {
	const response = createErrorResponse('method_not_allowed', 405, message);
	const headers = new Headers(response.headers);
	headers.set('Allow', 'POST, OPTIONS');
	return new Response(response.body, { status: response.status, headers });
}

export function tooManyRequests(message = 'Rate limit exceeded', retryAfter?: number): Response {
	return createErrorResponse('rate_limit_exceeded', 429, message, undefined, retryAfter);
}

export function badGateway(message = 'Upstream service error'): Response {
	return createErrorResponse('bad_gateway', 502, message);
}

export function serviceUnavailable(message = 'Service temporarily unavailable'): Response {
	return createErrorResponse('service_unavailable', 503, message);
}

export function internalServerError(message = 'Internal server error occurred'): Response {
	return createErrorResponse('internal_error', 500, message);
}
