import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const fixturePath = resolve(scriptDirectory, '../tests/fixtures/build-backend-responses.json');

export async function startBuildFixtureServer() {
  const fixtures = JSON.parse(await readFile(fixturePath, 'utf8'));
  const requests = [];
  const unexpectedRequests = [];

  const server = createServer((request, response) => {
    const pathname = new URL(request.url, 'http://127.0.0.1').pathname;
    if (request.method !== 'GET' || !Object.hasOwn(fixtures, pathname.slice(1)) || pathname === '/') {
      unexpectedRequests.push(pathname);
      response.writeHead(404);
      response.end();
      return;
    }

    requests.push(pathname);
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify(fixtures[pathname.slice(1)]));
  });

  await new Promise((resolveListen, rejectListen) => {
    server.once('error', rejectListen);
    server.listen(0, '127.0.0.1', () => {
      server.off('error', rejectListen);
      resolveListen();
    });
  });

  const address = server.address();
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    requests,
    unexpectedRequests,
    close: () => new Promise((resolveClose, rejectClose) => {
      server.close((error) => error ? rejectClose(error) : resolveClose());
    }),
  };
}
