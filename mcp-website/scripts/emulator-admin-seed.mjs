// Public, synthetic credentials for the local emulator only. Never use in cloud projects.
export async function seedLocalAdmin(auth,env = process.env) {
  if (env.GCLOUD_PROJECT !== 'demo-mcp-local' || env.FIREBASE_AUTH_EMULATOR_HOST !== '127.0.0.1:9099') {
    throw new Error('Admin seed requires the local Auth emulator (demo-mcp-local, 127.0.0.1:9099)')
  }
  const account = {
    email:'admin@test.it',
    password:'admin123', // NOSECRET: emulator-only public fixture
    displayName:'Local Test Admin',
    emailVerified:true,
    disabled:false,
  }
  let user
  try {
    user = await auth.getUserByEmail(account.email)
  } catch (error) {
    if (error.code !== 'auth/user-not-found') throw error
  }
  user = user
    ? await auth.updateUser(user.uid,account)
    : await auth.createUser({uid:'local-test-admin',...account})
  await auth.setCustomUserClaims(user.uid,{admin:true})
  return user
}
