const test = require("node:test")
const assert = require("node:assert/strict")
const { isCompletedPurchase } = require("../lib/purchase-statistics.cjs")

test("isCompletedPurchase accepts only string COMPLETED values in both fields", () => {
  assert.equal(isCompletedPurchase({ status: "COMPLETED", capture_status: "COMPLETED" }), true)
  assert.equal(isCompletedPurchase({ status: "completed", capture_status: "completed" }), true)
})

test("isCompletedPurchase rejects absent, malformed, and nonfinal fields", () => {
  for (const field of ["status", "capture_status"]) {
    const purchase = { status: "COMPLETED", capture_status: "COMPLETED" }
    delete purchase[field]
    assert.equal(isCompletedPurchase(purchase), false, `${field} missing`)
  }
  const badValues = [undefined, null, "PENDING", "FAILED", "DECLINED", "REFUNDED", "UNKNOWN", 17, true, " COMPLETED "]
  for (const field of ["status", "capture_status"]) {
    for (const value of badValues) {
      const purchase = { status: "COMPLETED", capture_status: "COMPLETED", [field]: value }
      assert.equal(isCompletedPurchase(purchase), false, `${field}=${String(value)}`)
    }
  }
  assert.equal(isCompletedPurchase(null), false)
  assert.equal(isCompletedPurchase(undefined), false)
})
