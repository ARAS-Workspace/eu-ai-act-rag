// SPDX-License-Identifier: MIT
/**
 *  █████╗ ██████╗  █████╗ ███████╗
 * ██╔══██╗██╔══██╗██╔══██╗██╔════╝
 * ███████║██████╔╝███████║███████╗
 * ██╔══██║██╔══██╗██╔══██║╚════██║
 * ██║  ██║██║  ██║██║  ██║███████║
 * ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
 *
 * Copyright (C) 2026 Riza Emre ARAS <r.emrearas@proton.me>
 * EU AI Act RAG Worker — MIT License
 */

/**
 * EU AI Act RAG Worker - Main Entry Point
 * @version 1.0.0
 */

import type { Env, ChatRequest, ChatResponse } from './types';
import { CONFIG } from './config';
import { badRequest, badGateway, internalServerError, tooManyRequests, notFound, methodNotAllowed } from './utils/errors';
import { logError, logInfo, logWarn } from './utils/logging';
import { validateChatRequest } from './validation/request';
import { checkRateLimits } from './middleware/ratelimit';
import { getTranslations, parseLocale, type Locale } from './translations';
import { AutoRAGManager } from './ai';
import { SYSTEM_PROMPT } from './ai/prompts';

const CORS_HEADERS = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'POST, OPTIONS',
	'Access-Control-Allow-Headers': 'Content-Type',
	'Access-Control-Max-Age': '86400',
};

// noinspection JSUnusedGlobalSymbols
export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const startTime = Date.now();
		const url = new URL(request.url);
		const method = request.method;

		try {
			// 1. CORS preflight
			if (method === 'OPTIONS') {
				return new Response(null, { status: 204, headers: CORS_HEADERS });
			}

			// 2. Endpoint check
			if (url.pathname !== '/api/v1/chat/completions' && url.pathname !== '/') {
				const t = getTranslations('en').errors;
				return notFound(t.endpointNotFound);
			}

			// 3. Method check
			if (method !== 'POST') {
				const t = getTranslations('en').errors;
				return methodNotAllowed(t.methodNotAllowed);
			}

			// 4. Body size check
			const contentLength = request.headers.get('Content-Length');
			if (contentLength && parseInt(contentLength) > CONFIG.validation.maxRequestBodySize) {
				logWarn('[RAG-WORKER] Request body too large', { size: parseInt(contentLength) }, env);
				const t = getTranslations('en').errors;
				return badRequest(t.requestBodyTooLarge);
			}

			// 5. Rate limit check
			const rateLimitResult = await checkRateLimits(request, env);
			if (!rateLimitResult.allowed) {
				logWarn('[RAG-WORKER] Rate limit exceeded', { remaining: rateLimitResult.remaining }, env);
				const t = getTranslations('en').errors;
				return tooManyRequests(t.rateLimitExceeded, rateLimitResult.retryAfter);
			}

			// 6. Parse request body
			let body: unknown;
			try {
				body = await request.json();
			} catch (error) {
				logError('[RAG-WORKER] JSON parse error', error, env);
				const t = getTranslations('en').errors;
				return badRequest(t.invalidJson);
			}

			// 7. Extract locale
			const locale: Locale = parseLocale((body as Record<string, unknown>)?.locale);
			const t = getTranslations(locale).errors;

			// 8. Validate request
			let chatRequest: ChatRequest;
			try {
				chatRequest = validateChatRequest(body, locale);
			} catch (error) {
				logError('[RAG-WORKER] Validation error', error, env);
				return badRequest(
					error instanceof Error ? error.message : t.validationFailed,
					(error as { validationErrors?: unknown }).validationErrors,
				);
			}

			logInfo(
				'[RAG-WORKER] Processing request',
				{ locale, messagesCount: chatRequest.messages.length },
				env,
			);

			// 9. Extract last user message as query
			const lastUserMessage = [...chatRequest.messages].reverse().find((m) => m.role === 'user');
			if (!lastUserMessage) {
				return badRequest(t.validationFailed);
			}

			// 10. Call AutoRAG
			const autorag = new AutoRAGManager(env.AI, env.AISEARCH_NAME);
			let searchResponse;

			try {
				searchResponse = await autorag.search(lastUserMessage.content, SYSTEM_PROMPT, chatRequest.searchOptions);
			} catch (error) {
				logError('[RAG-WORKER] AutoRAG error', error, env);
				return badGateway(error instanceof Error ? `AI service error: ${error.message}` : t.upstreamConnectionFailed);
			}

			// 11. Build response
			const duration = Date.now() - startTime;
			const response: ChatResponse = {
				response: searchResponse.response || t.emptyResponse,
				sources: searchResponse.sources,
				metadata: {
					search_query: searchResponse.searchQuery,
					duration_ms: duration,
					timestamp: Date.now(),
				},
			};

			logInfo('[RAG-WORKER] Request completed', { duration_ms: duration }, env);

			return new Response(JSON.stringify(response, null, 2), {
				status: 200,
				headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
			});
		} catch (error) {
			logError('[RAG-WORKER] Unexpected error', error, env);
			const t = getTranslations('en').errors;
			return internalServerError(t.unexpectedError);
		}
	},
};
