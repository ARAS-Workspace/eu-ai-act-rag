// SPDX-License-Identifier: MIT

/**
 * Translations for EU AI Act RAG Worker
 */

export type Locale = 'en' | 'tr';

export interface ErrorMessages {
	invalidRequest: string;
	requestBodyTooLarge: string;
	invalidJson: string;
	validationFailed: string;
	endpointNotFound: string;
	methodNotAllowed: string;
	rateLimitExceeded: string;
	turnstileRequired: string;
	turnstileInvalid: string;
	upstreamConnectionFailed: string;
	serviceUnavailable: string;
	unexpectedError: string;
	emptyResponse: string;
}

export interface ValidationMessages {
	validationSummary: string;
	messagesRequired: string;
	messagesArrayRequired: string;
	messagesEmpty: string;
	messagesLimitExceeded: (limit: number) => string;
	messageObjectRequired: (index: number) => string;
	roleRequired: (index: number) => string;
	roleInvalid: (index: number) => string;
	contentRequired: (index: number) => string;
	contentStringRequired: (index: number) => string;
	contentEmpty: (index: number) => string;
	contentTooLong: (index: number, limit: number) => string;
	streamBooleanRequired: string;
	searchOptionsObjectRequired: string;
	searchOptionsModelInvalid: string;
	searchOptionsRewriteQueryBooleanRequired: string;
	searchOptionsReRankingBooleanRequired: string;
	searchOptionsMaxResultsInvalid: string;
	searchOptionsScoreThresholdInvalid: string;
}

export interface Translations {
	errors: ErrorMessages;
	validation: ValidationMessages;
}

const translations: Record<Locale, Translations> = {
	en: {
		errors: {
			invalidRequest: 'Invalid request',
			requestBodyTooLarge: 'Request body too large',
			invalidJson: 'Invalid JSON format',
			validationFailed: 'Request validation failed',
			endpointNotFound: 'Endpoint not found. Use POST /api/v1/chat/completions',
			methodNotAllowed: 'Only POST and OPTIONS requests are allowed',
			rateLimitExceeded: 'Rate limit exceeded. Please try again later',
			turnstileRequired: 'Security verification required',
			turnstileInvalid: 'Security verification failed. Please try again',
			upstreamConnectionFailed: 'Failed to connect to AI service',
			serviceUnavailable: 'Service temporarily unavailable',
			unexpectedError: 'An unexpected error occurred',
			emptyResponse: 'Sorry, unable to generate a response. Please try again.',
		},
		validation: {
			validationSummary: 'Request validation failed',
			messagesRequired: 'messages field is required',
			messagesArrayRequired: 'messages must be an array',
			messagesEmpty: 'messages array must contain at least one message',
			messagesLimitExceeded: (limit) => `messages array cannot exceed ${limit} messages`,
			messageObjectRequired: (index) => `messages[${index}] must be an object`,
			roleRequired: (index) => `messages[${index}].role is required`,
			roleInvalid: (index) => `messages[${index}].role must be "user" or "assistant"`,
			contentRequired: (index) => `messages[${index}].content is required`,
			contentStringRequired: (index) => `messages[${index}].content must be a string`,
			contentEmpty: (index) => `messages[${index}].content cannot be empty`,
			contentTooLong: (index, limit) => `messages[${index}].content cannot exceed ${limit} characters`,
			streamBooleanRequired: 'stream must be a boolean',
			searchOptionsObjectRequired: 'searchOptions must be an object',
			searchOptionsModelInvalid: 'searchOptions.model must be a valid Cloudflare model ID',
			searchOptionsRewriteQueryBooleanRequired: 'searchOptions.rewriteQuery must be a boolean',
			searchOptionsReRankingBooleanRequired: 'searchOptions.reRanking must be a boolean',
			searchOptionsMaxResultsInvalid: 'searchOptions.maxResults must be an integer between 1 and 50',
			searchOptionsScoreThresholdInvalid: 'searchOptions.scoreThreshold must be a number between 0 and 1',
		},
	},
	tr: {
		errors: {
			invalidRequest: 'Gecersiz istek',
			requestBodyTooLarge: 'Istek boyutu cok buyuk',
			invalidJson: 'Gecersiz JSON formati',
			validationFailed: 'Istek dogrulamasi basarisiz',
			endpointNotFound: 'Endpoint bulunamadi. POST /api/v1/chat/completions kullanin',
			methodNotAllowed: 'Sadece POST ve OPTIONS istekleri kabul edilir',
			rateLimitExceeded: 'Istek limiti asildi. Lutfen daha sonra tekrar deneyin',
			turnstileRequired: 'Guvenlik dogrulamasi gerekli',
			turnstileInvalid: 'Guvenlik dogrulamasi basarisiz. Lutfen tekrar deneyin',
			upstreamConnectionFailed: 'AI servisine baglanilamadi',
			serviceUnavailable: 'Servis gecici olarak kullanilamiyor',
			unexpectedError: 'Beklenmeyen bir hata olustu',
			emptyResponse: 'Uzgunum, yanit olusturulamadi. Lutfen tekrar deneyin.',
		},
		validation: {
			validationSummary: 'Istek dogrulamasi basarisiz',
			messagesRequired: 'messages alani zorunludur',
			messagesArrayRequired: 'messages bir dizi olmalidir',
			messagesEmpty: 'messages dizisi en az bir mesaj icermelidir',
			messagesLimitExceeded: (limit) => `messages dizisi maksimum ${limit} mesaj icerebilir`,
			messageObjectRequired: (index) => `messages[${index}] bir nesne olmalidir`,
			roleRequired: (index) => `messages[${index}].role zorunludur`,
			roleInvalid: (index) => `messages[${index}].role "user" veya "assistant" olmalidir`,
			contentRequired: (index) => `messages[${index}].content zorunludur`,
			contentStringRequired: (index) => `messages[${index}].content bir metin olmalidir`,
			contentEmpty: (index) => `messages[${index}].content bos olamaz`,
			contentTooLong: (index, limit) => `messages[${index}].content maksimum ${limit} karakter olabilir`,
			streamBooleanRequired: 'stream bir boolean değer olmalıdır',
			searchOptionsObjectRequired: 'searchOptions bir nesne olmalıdır',
			searchOptionsModelInvalid: 'searchOptions.model geçerli bir Cloudflare model ID olmalıdır',
			searchOptionsRewriteQueryBooleanRequired: 'searchOptions.rewriteQuery bir boolean değer olmalıdır',
			searchOptionsReRankingBooleanRequired: 'searchOptions.reRanking bir boolean değer olmalıdır',
			searchOptionsMaxResultsInvalid: 'searchOptions.maxResults 1 ile 50 arasında bir tamsayı olmalıdır',
			searchOptionsScoreThresholdInvalid: 'searchOptions.scoreThreshold 0 ile 1 arasında bir sayı olmalıdır',
		},
	},
};

export function getTranslations(locale: Locale = 'en'): Translations {
	return translations[locale] || translations.en;
}

export function parseLocale(locale?: unknown): Locale {
	if (typeof locale === 'string' && (locale === 'en' || locale === 'tr')) {
		return locale;
	}
	return 'en';
}
