import test from "node:test"
import assert from "node:assert/strict"

import { detectEmailTypo } from "./emailValidation.js"

test("detectEmailTypo suggests gmail.com for gmial.com", () => {
  const result = detectEmailTypo("utente@gmial.com")
  assert.ok(result)
  assert.equal(result.typedDomain, "gmial.com")
  assert.equal(result.suggestedDomain, "gmail.com")
})

test("detectEmailTypo returns null for common valid domain", () => {
  const result = detectEmailTypo("utente@gmail.com")
  assert.equal(result, null)
})

test("detectEmailTypo returns null when domain is too different", () => {
  const result = detectEmailTypo("utente@example.org")
  assert.equal(result, null)
})
