# Feature Audit Summary Table

## All 51 Features - Classification & Status

| #   | Feature                   | Status    | Category         | Reason                                             |
| --- | ------------------------- | --------- | ---------------- | -------------------------------------------------- |
| 1   | affordability_score       | ❌ INVALID | Agent Logic Leak | Pre-computes Agent 2's affordability determination |
| 2   | availability_encoded      | ✅ VALID   | Raw Data         | Simple availability encoding                       |
| 3   | brand_frequency           | ⚠️ WEAK    | Popularity Bias  | Dataset statistic, use for filtering only          |
| 4   | category_frequency        | ⚠️ WEAK    | Popularity Bias  | Dataset statistic, use for filtering only          |
| 5   | color_options_count       | ✅ VALID   | Raw Data         | Color variant count                                |
| 6   | condition_encoded         | ✅ VALID   | Raw Data         | Product condition encoding                         |
| 7   | conversion_probability    | ❌ INVALID | Model Leak       | Pre-predicts MODEL's output                        |
| 8   | deal_score                | ❌ INVALID | Agent Logic Leak | Pre-computes Agent 2.5's deal assessment           |
| 9   | description_length        | ✅ VALID   | Raw Data         | Description character count                        |
| 10  | description_word_count    | ⚠️ WEAK    | Redundant        | Correlated with description_length                 |
| 11  | discount_amount_TND       | ✅ VALID   | Raw Data         | Absolute discount value                            |
| 12  | discount_tier             | ⚠️ WEAK    | Redundant        | Derived from discount_percentage                   |
| 13  | features_count            | ✅ VALID   | Metadata         | Product feature bullet count                       |
| 14  | has_brand_model           | ✅ VALID   | Metadata         | Data completeness indicator                        |
| 15  | has_detailed_description  | ✅ VALID   | Metadata         | Data completeness indicator                        |
| 16  | has_discount              | ✅ VALID   | Raw Data         | Boolean discount flag                              |
| 17  | has_free_shipping         | ✅ VALID   | Raw Data         | Free shipping flag                                 |
| 18  | has_main_image            | ✅ VALID   | Metadata         | Data completeness indicator                        |
| 19  | has_multiple_colors       | ⚠️ WEAK    | Redundant        | Derived from color_options_count                   |
| 20  | has_warranty              | ✅ VALID   | Raw Data         | Warranty flag                                      |
| 21  | image_count               | ✅ VALID   | Metadata         | Image count                                        |
| 22  | info_completeness_score   | ⚠️ WEAK    | Composite        | Low-impact aggregation                             |
| 23  | is_bestseller             | ❌ INVALID | Popularity Bias  | Hardcoded popularity advantage                     |
| 24  | is_budget_friendly        | ⚠️ WEAK    | Redundant        | Derived from price_category                        |
| 25  | is_major_brand            | ❌ INVALID | Popularity Bias  | Top-20 brand bias                                  |
| 26  | is_new_product            | ⚠️ WEAK    | Low Impact       | Arbitrary threshold                                |
| 27  | is_premium_product        | ⚠️ WEAK    | Composite        | Redundant combination                              |
| 28  | name_length               | ✅ VALID   | Raw Data         | Name character count                               |
| 29  | name_word_count           | ⚠️ WEAK    | Redundant        | Correlated with name_length                        |
| 30  | popularity_score          | ❌ INVALID | Popularity Bias  | Explicit popularity injection                      |
| 31  | price_category            | ✅ VALID   | Derived          | Budget/Mid/Premium/Luxury binning                  |
| 32  | price_normalized          | ✅ VALID   | Derived          | Z-score normalization                              |
| 33  | price_tier                | ⚠️ WEAK    | Redundant        | Overlaps with price_normalized                     |
| 34  | purchase_readiness        | ❌ INVALID | Model Leak       | Pre-computes purchase likelihood                   |
| 35  | quality_score             | ❌ INVALID | Agent Logic Leak | Pre-computes Agent 3's quality assessment          |
| 36  | rating_category           | ✅ VALID   | Derived          | Rating tier binning                                |
| 37  | rating_confidence         | ❌ INVALID | Model Leak       | Pre-weights rating by popularity                   |
| 38  | rating_normalized         | ✅ VALID   | Derived          | Rating normalization                               |
| 39  | recommendation_confidence | ❌ INVALID | Model Leak       | Pre-predicts recommendation strength               |
| 40  | reviews_log               | ✅ VALID   | Derived          | Log-scaled review count                            |
| 41  | satisfaction_proxy        | ❌ INVALID | Model Leak       | Duplicate of rating_confidence                     |
| 42  | seller_product_count      | ⚠️ WEAK    | Popularity Bias  | Seller-level bias                                  |
| 43  | shipping_cost             | ✅ VALID   | Raw Data         | Shipping cost                                      |
| 44  | specifications_count      | ✅ VALID   | Metadata         | Specification count                                |
| 45  | stock_level               | ✅ VALID   | Derived          | Stock quantity binning                             |
| 46  | thompson_alpha_hint       | ❌ INVALID | RL CONFLICT      | Violates RL exploration principle                  |
| 47  | thompson_beta_hint        | ❌ INVALID | RL CONFLICT      | Violates RL exploration principle                  |
| 48  | urgency_score             | ❌ INVALID | Agent Logic Leak | Pre-computes urgency signal                        |
| 49  | value_for_money           | ❌ INVALID | Agent Logic Leak | Pre-computes Agent 2's value assessment            |
| 50  | value_indicator           | ❌ INVALID | Model Leak       | Redundant composite                                |
| 51  | warranty_months           | ✅ VALID   | Raw Data         | Warranty duration                                  |

---

## Summary Statistics

- ✅ **VALID**: 25 features (49%)
- ❌ **INVALID**: 15 features (29%)
- ⚠️ **WEAK**: 11 features (22%)

---

## Recommended Action

**DELETE 26 features** (15 INVALID + 11 WEAK)

**KEEP 25 features** (all VALID features)

---

## Features to DELETE (26)

### Thompson Sampling Conflicts (2)
- thompson_alpha_hint
- thompson_beta_hint

### Popularity Bias (4)
- popularity_score
- is_bestseller
- is_major_brand

### Model Outcome Leakage (5)
- conversion_probability
- purchase_readiness
- recommendation_confidence
- rating_confidence
- satisfaction_proxy

### Agent Logic Duplication (5)
- quality_score
- value_for_money
- deal_score
- affordability_score
- urgency_score
- value_indicator

### Redundant/Weak (10)
- description_word_count
- name_word_count
- has_multiple_colors
- discount_tier
- is_budget_friendly
- is_new_product
- is_premium_product
- info_completeness_score
- price_tier
- seller_product_count

---

## Features to KEEP (25)

### Metadata (5)
- has_brand_model
- has_detailed_description
- has_main_image
- image_count
- specifications_count

### Text (2)
- name_length
- description_length

### Price (5)
- price_normalized
- price_category
- has_discount
- discount_amount_TND
- features_count

### Rating (3)
- rating_normalized
- rating_category
- reviews_log

### Inventory (4)
- availability_encoded
- stock_level
- condition_encoded
- color_options_count

### Logistics (4)
- has_free_shipping
- shipping_cost
- has_warranty
- warranty_months

### Dataset Stats (2) - USE CAREFULLY
- category_frequency (filtering only, NOT ranking)
- brand_frequency (filtering only, NOT ranking)
