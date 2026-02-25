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
 * EU AI Act RAG Worker Configuration
 */

export const CONFIG = {
	/**
	 * AI Search / AutoRAG Settings
	 * @see https://developers.cloudflare.com/ai-search/
	 */
	aisearch: {
		/**
		 * LLM model for AI Search response generation
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/models/
		 */
		model: '@cf/meta/llama-3.3-70b-instruct-fp8-fast',

		/**
		 * Enable query rewriting for better search results
		 * Transforms user queries into search-optimized queries using an LLM
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/query-rewriting/
		 */
		rewriteQuery: true,

		/**
		 * Maximum number of search results to return (1-50)
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/retrieval-configuration/
		 */
		maxResults: 20,

		/**
		 * Semantic reranking configuration
		 * Reranks search results using specialized reranking models for improved relevance
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/reranking/
		 */
		reranking: {
			enabled: true,
			model: '@cf/baai/bge-reranker-base',
		},

		/**
		 * Ranking options for search result filtering
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/retrieval-configuration/
		 */
		ranking: {
			/**
			 * Minimum score threshold for search results (0-1 range)
			 *
			 * Tuning guide:
			 * - 0.3-0.4: Higher recall (more results, some may be less relevant)
			 * - 0.4-0.5: Balanced precision/recall
			 * - 0.5-0.6: Higher precision (fewer but more relevant results)
			 */
			scoreThreshold: 0.4,
		},

		/**
		 * Indexing Configuration (set at AI Search instance level, not runtime)
		 *
		 * Configured in Cloudflare Dashboard > AI Search > Settings:
		 *
		 * Embedding Model: @cf/qwen/qwen3-embedding-0.6b (1024 dimensions, 4096 input tokens)
		 * Chunk Size: 512 tokens
		 * Chunk Overlap: 10%
		 * Vector Store: Cloudflare Vectorize (1024 dimensions)
		 * Object Storage: Cloudflare R2 (eu-ai-act-rag bucket)
		 *
		 * @see https://developers.cloudflare.com/ai-search/configuration/chunking/
		 */
	},

	/**
	 * Request Validation Limits
	 */
	validation: {
		maxMessageLength: 4096,
		maxMessagesPerRequest: 20,
		maxRequestBodySize: 20480, // 20 KB
	},

	/**
	 * Rate Limiting Configuration
	 */
	rateLimit: {
		requestsPerMinute: 10,
		requestsPerHour: 100,
		requestsPerDay: 500,
	},

	/**
	 * Localization Settings
	 */
	localization: {
		defaultLocale: 'en' as 'en' | 'tr',
		supportedLocales: ['en', 'tr'] as const,
	},
} as const;
