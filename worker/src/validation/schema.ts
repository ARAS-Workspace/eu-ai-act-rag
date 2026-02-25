// SPDX-License-Identifier: MIT

/**
 * JSON Schema definition and ajv validator for ChatRequest
 */

import Ajv, { type ErrorObject } from 'ajv';
import type { ValidationError } from '../types';
import { CONFIG } from '../config';
import { getTranslations, type Locale } from '../translations';

export const VALID_MODELS = [
	'@cf/meta/llama-3.3-70b-instruct-fp8-fast',
	'@cf/meta/llama-3.1-8b-instruct',
	'@cf/meta/llama-3.1-70b-instruct',
	'@cf/mistral/mistral-7b-instruct-v0.1',
	'@cf/google/gemma-7b-it',
	'@cf/qwen/qwen1.5-7b-chat-awq',
] as const;

export const chatRequestSchema = {
	type: 'object',
	properties: {
		messages: {
			type: 'array',
			minItems: 1,
			maxItems: CONFIG.validation.maxMessagesPerRequest,
			items: {
				type: 'object',
				properties: {
					role: { type: 'string', enum: ['user', 'assistant'] },
					content: {
						type: 'string',
						minLength: 1,
						maxLength: CONFIG.validation.maxMessageLength,
						pattern: '^(?!\\s*$)',
					},
				},
				required: ['role', 'content'],
				additionalProperties: false,
			},
		},
		stream: { type: 'boolean' },
		locale: { type: 'string', enum: [...CONFIG.localization.supportedLocales] },
		searchOptions: {
			type: 'object',
			properties: {
				model: { type: 'string', enum: [...VALID_MODELS] },
				rewriteQuery: { type: 'boolean' },
				reRanking: { type: 'boolean' },
				maxResults: { type: 'integer', minimum: 1, maximum: 50 },
				scoreThreshold: { type: 'number', minimum: 0, maximum: 1 },
			},
			additionalProperties: false,
		},
	},
	required: ['messages'],
	additionalProperties: false,
} as const;

const ajv = new Ajv({ allErrors: true });
export const compiledValidator = ajv.compile(chatRequestSchema);

export function mapAjvErrors(errors: ErrorObject[], locale: Locale): ValidationError[] {
	const t = getTranslations(locale).validation;
	const result: ValidationError[] = [];

	for (const err of errors) {
		const path = err.instancePath;

		// --- top-level required ---
		if (err.keyword === 'required' && err.params.missingProperty === 'messages') {
			result.push({ field: 'messages', message: t.messagesRequired });
			continue;
		}

		// --- messages array ---
		if (path === '/messages') {
			if (err.keyword === 'type') {
				result.push({ field: 'messages', message: t.messagesArrayRequired });
			} else if (err.keyword === 'minItems') {
				result.push({ field: 'messages', message: t.messagesEmpty });
			} else if (err.keyword === 'maxItems') {
				result.push({ field: 'messages', message: t.messagesLimitExceeded(CONFIG.validation.maxMessagesPerRequest), value: err.data });
			}
			continue;
		}

		// --- messages[N] item-level required ---
		const itemMatch = path.match(/^\/messages\/(\d+)$/);
		if (itemMatch) {
			const index = parseInt(itemMatch[1]);
			if (err.keyword === 'required') {
				const missing = err.params.missingProperty as string;
				if (missing === 'role') {
					result.push({ field: `messages[${index}].role`, message: t.roleRequired(index) });
				} else if (missing === 'content') {
					result.push({ field: `messages[${index}].content`, message: t.contentRequired(index) });
				}
			} else if (err.keyword === 'type') {
				result.push({ field: `messages[${index}]`, message: t.messageObjectRequired(index) });
			}
			continue;
		}

		// --- messages[N].role ---
		const roleMatch = path.match(/^\/messages\/(\d+)\/role$/);
		if (roleMatch) {
			const index = parseInt(roleMatch[1]);
			if (err.keyword === 'enum') {
				result.push({ field: `messages[${index}].role`, message: t.roleInvalid(index), value: err.data });
			} else {
				result.push({ field: `messages[${index}].role`, message: t.roleRequired(index), value: err.data });
			}
			continue;
		}

		// --- messages[N].content ---
		const contentMatch = path.match(/^\/messages\/(\d+)\/content$/);
		if (contentMatch) {
			const index = parseInt(contentMatch[1]);
			if (err.keyword === 'type') {
				result.push({ field: `messages[${index}].content`, message: t.contentStringRequired(index), value: err.data });
			} else if (err.keyword === 'minLength' || err.keyword === 'pattern') {
				result.push({ field: `messages[${index}].content`, message: t.contentEmpty(index), value: err.data });
			} else if (err.keyword === 'maxLength') {
				result.push({ field: `messages[${index}].content`, message: t.contentTooLong(index, CONFIG.validation.maxMessageLength), value: err.data });
			}
			continue;
		}

		// --- stream ---
		if (path === '/stream') {
			result.push({ field: 'stream', message: t.streamBooleanRequired, value: err.data });
			continue;
		}

		// --- searchOptions ---
		if (path === '/searchOptions') {
			result.push({ field: 'searchOptions', message: t.searchOptionsObjectRequired, value: err.data });
			continue;
		}
		if (path.startsWith('/searchOptions/')) {
			const field = path.replace('/searchOptions/', 'searchOptions.');
			const key = path.replace('/searchOptions/', '');
			const messageMap: Record<string, string> = {
				model: t.searchOptionsModelInvalid,
				rewriteQuery: t.searchOptionsRewriteQueryBooleanRequired,
				reRanking: t.searchOptionsReRankingBooleanRequired,
				maxResults: t.searchOptionsMaxResultsInvalid,
				scoreThreshold: t.searchOptionsScoreThresholdInvalid,
			};
			result.push({ field, message: messageMap[key] ?? err.message ?? 'Validation error', value: err.data });
			continue;
		}

		// --- fallback ---
		result.push({
			field: path.replace(/^\//, '').replace(/\//g, '.') || (err.params.missingProperty as string) || 'unknown',
			message: err.message ?? 'Validation error',
			value: err.data,
		});
	}

	return result;
}
