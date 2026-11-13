function isCompletedPurchase(purchase) {
  return typeof purchase?.status === "string"
    && typeof purchase?.capture_status === "string"
    && purchase.status.toUpperCase() === "COMPLETED"
    && purchase.capture_status.toUpperCase() === "COMPLETED"
}

module.exports = { isCompletedPurchase }
