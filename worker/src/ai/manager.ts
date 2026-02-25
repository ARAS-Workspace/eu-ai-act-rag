// SPDX-License-Identifier: MIT

/**
 * AI Search Manager
 *
 * Manages AI Search interactions via Cloudflare Workers AI binding.
 * Uses autorag() API (aiSearch.get() is not yet supported in wrangler dev runtime).
 */

import { CONFIG } from '../config';

export interface SearchOptions {
	model?: string;
	rewriteQuery?: boolean;
	reRanking?: boolean;
	maxResults?: number;
	scoreThreshold?: number;
}

export interface SearchResponse {
	response: string;
	searchQuery: string;
	sources: Array<{
		filename: string;
		score: number;
		content: string;
	}>;
}

export class AutoRAGManager {
	private readonly ai: Ai;
	private readonly instanceName: string;

	constructor(ai: Ai, instanceName: string) {
		this.ai = ai;
		this.instanceName = instanceName;
	}

	/**
	 * Execute AI Search query with full parameter customization
	 *
	 * @param query - User's search query
	 * @param systemPrompt - System prompt for response generation
	 * @param options - Override default search options
	 * @returns Formatted search response with sources
	 */
	async search(query: string, systemPrompt: string, options?: SearchOptions): Promise<SearchResponse> {
		const instance = this.ai.autorag(this.instanceName);

		const result = await instance.aiSearch({
			query,
			system_prompt: systemPrompt,
			stream: false as const,
			max_num_results: options?.maxResults || CONFIG.aisearch.maxResults,
			ranking_options: {
				score_threshold: options?.scoreThreshold || CONFIG.aisearch.ranking.scoreThreshold,
			},
			reranking: {
				enabled: options?.reRanking ?? CONFIG.aisearch.reranking.enabled,
				model: CONFIG.aisearch.reranking.model,
			},
			rewrite_query: options?.rewriteQuery ?? CONFIG.aisearch.rewriteQuery,
		});

		const sources =
			result.data?.map((item) => ({
				filename: item.filename,
				score: item.score,
				content: item.content?.map((c: { text: string }) => c.text).join('\n') || '',
			})) || [];

		return {
			response: result.response || '',
			searchQuery: result.search_query || '',
			sources,
		};
	}
}
