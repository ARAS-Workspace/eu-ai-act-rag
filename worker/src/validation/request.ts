// SPDX-License-Identifier: MIT

/**
 * Request Validation (ajv JSON Schema)
 */

import type { ChatRequest, ValidationError } from '../types';
import { getTranslations, type Locale } from '../translations';
import { compiledValidator, mapAjvErrors } from './schema';

export function validateChatRequest(body: unknown, locale: Locale = 'en'): ChatRequest {
	const t = getTranslations(locale).validation;

	if (!body || typeof body !== 'object') {
		throw new Error('Request body must be a JSON object');
	}

	const valid = compiledValidator(body);

	if (!valid) {
		const errors: ValidationError[] = mapAjvErrors(compiledValidator.errors ?? [], locale);
		const errorMessage = t.validationSummary + ': ' + errors.map((e) => `${e.field}: ${e.message}`).join(', ');
		const error = new Error(errorMessage) as Error & { validationErrors: ValidationError[] };
		error.validationErrors = errors;
		throw error;
	}

	return body as ChatRequest;
}
