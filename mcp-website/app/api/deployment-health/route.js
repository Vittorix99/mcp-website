export const dynamic = 'force-dynamic'

export async function GET() {
  const sha = process.env.NEXT_PUBLIC_RELEASE_SHA || ''
  const tree = process.env.NEXT_PUBLIC_SITE_TREE || ''
  const digest = process.env.NEXT_PUBLIC_CONFIGURATION_DIGEST || ''
  if (!/^[0-9a-f]{40}$/.test(sha) || !/^[0-9a-f]{64}$/.test(tree) || !/^[0-9a-f]{64}$/.test(digest)) {
    return Response.json({status:'unversioned'}, {status:503, headers:{'Cache-Control':'no-store'}})
  }
  return Response.json({
    status:'ok', environment:process.env.NEXT_PUBLIC_ENV,
    project_id:process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    release_sha:sha, site_tree:tree, configuration_digest:digest,
  }, {headers:{'Cache-Control':'no-store'}})
}
