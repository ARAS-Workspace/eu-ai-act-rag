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
 * EU AI Act RAG Playground — MIT License
 */

/**
 * EU AI Act RAG Playground
 *
 * Cloudflare Worker that serves as a reverse-proxy to Streamlit container.
 */

import { Container, getContainer } from '@cloudflare/containers';
import { Hono } from 'hono';

// Streamlit Container Configuration
export class StreamlitContainer extends Container<Env> {
	defaultPort = 8501;
	sleepAfter = '5m';
	enableInternet = true;

	override onStart() {
		console.log('Streamlit container started');
	}

	override onStop() {
		console.log('Streamlit container stopped');
	}

	override onError(error: unknown) {
		console.error('Streamlit container error:', error);
	}
}

const app = new Hono<{ Bindings: Env }>();

// Health check endpoint
app.get('/health', (c) => {
	return c.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Public config endpoint — serves non-secret client configuration
app.get('/api/config', (c) => {
	return c.json({
		turnstileSiteKey: c.env.TURNSTILE_SITE_KEY || '',
	});
});

// Reverse proxy all requests to Streamlit container
app.all('*', async (c) => {
	const container = getContainer(c.env.STREAMLIT);
	return await container.fetch(c.req.raw);
});

export default app;
