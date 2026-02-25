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

import {SearchOptions} from "./ai";

/**
 * EU AI Act RAG Worker - Type Definitions
 */

// ========================================
// Cloudflare Workers Environment
// ========================================

export interface Env {
	AISEARCH_NAME: string;
	ENVIRONMENT?: string;
	EU_AI_ACT_RAG_WORKER_KV: KVNamespace;
	AI: Ai;
}

// ========================================
// Request/Response Types
// ========================================

export interface ChatRequest {
	messages: Array<{
		role: 'user' | 'assistant';
		content: string;
	}>;
	stream?: boolean;
	locale?: string;
	searchOptions?: SearchOptions;
}

export interface ChatResponse {
	response: string;
	sources: Array<{
		filename: string;
		score: number;
		content: string;
	}>;
	metadata: {
		search_query: string;
		duration_ms: number;
		timestamp: number;
	};
}

// ========================================
// Error Types
// ========================================

export interface ErrorResponse {
	error: {
		type: string;
		message: string;
		details?: unknown;
	};
	status: number;
	retryAfter?: number;
}

export interface ValidationError {
	field: string;
	message: string;
	value?: unknown;
}

// ========================================
// Rate Limiting Types
// ========================================

export interface RateLimitResult {
	allowed: boolean;
	remaining: number;
	resetAt: number;
	retryAfter?: number;
}
