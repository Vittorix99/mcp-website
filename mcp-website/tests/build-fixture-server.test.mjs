import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { startBuildFixtureServer } from '../scripts/build-fixture-server.mjs';
import fixtures from './fixtures/build-backend-responses.json' with { type: 'json' };

let server;
after(async () => {
  if (server) await server.close();
});

test('serves the configured backend fixtures from localhost', async () => {
  server = await startBuildFixtureServer();
  assert.match(server.baseUrl, /^http:\/\/127\.0\.0\.1:\d+$/);

  for (const [endpoint, payload] of Object.entries(fixtures)) {
    const response = await fetch(`${server.baseUrl}/${endpoint}`);
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /application\/json/);
    assert.deepEqual(await response.json(), payload);
  }

  assert.equal(server.requests.length, Object.keys(fixtures).length);
  assert.deepEqual(server.unexpectedRequests, []);
});

test('records unknown paths and non-GET requests as unexpected', async () => {
  const unknown = await fetch(`${server.baseUrl}/not_an_endpoint`);
  assert.equal(unknown.status, 404);

  const post = await fetch(`${server.baseUrl}/get_all_events`, { method: 'POST' });
  assert.equal(post.status, 404);
  assert.deepEqual(server.unexpectedRequests, ['/not_an_endpoint', '/get_all_events']);
});

test('allows query parameters for known view endpoints', async () => {
  const response = await fetch(`${server.baseUrl}/get_all_events?view=home`);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), fixtures.get_all_events);
  assert.deepEqual(server.unexpectedRequests, ['/not_an_endpoint', '/get_all_events']);
});
