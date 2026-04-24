export const dynamic = "force-dynamic";

async function forward(request, context) {
  const ENV = process.env.NEXT_PUBLIC_ENV || "local";
  const SERVER_BASE_URL =
    ENV === "production"
      ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
      : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1";

  const params = await context.params;
  const path = Array.isArray(params?.path) ? params.path.join("/") : "";
  const url = new URL(request.url);
  const target = `${SERVER_BASE_URL}/${path}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const method = request.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);
  const body = hasBody ? await request.arrayBuffer() : undefined;

  const response = await fetch(target, {
    method,
    headers,
    body,
    redirect: "manual",
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

export function GET(request, context) {
  return forward(request, context);
}

export function POST(request, context) {
  return forward(request, context);
}

export function PUT(request, context) {
  return forward(request, context);
}

export function DELETE(request, context) {
  return forward(request, context);
}
