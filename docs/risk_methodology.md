# Rule-Based Credit Risk Methodology

## 1. Purpose

The Banking Loan Risk Analysis application uses a transparent
rule-based scoring system to classify customers into:

- LOW
- MEDIUM
- HIGH

The classification is intended to help analysts prioritize
customers for review based on observed credit and repayment
behaviour.

This is not a machine learning model.

---

## 2. Risk Indicators

The risk score uses four behavioural indicators:

1. Delay frequency
2. Maximum delay severity
3. Latest credit utilization
4. Six-month payment-to-bill ratio

Demographic attributes are not used in the risk score.

The historical field `default_next_month` is also not used
as an input to the risk score. It is used only to validate
the resulting risk bands.

---

## 3. Delay Frequency Score

The number of months containing a positive repayment delay
is represented by `delay_month_count`.

| Delayed Months | Score |
|---|---:|
| 0 | 0 |
| 1 | 1 |
| 2 | 2 |
| 3 or more | 3 |

Historical analysis showed that default rates increased
substantially as the number of delayed months increased.

---

## 4. Delay Severity Score

The most severe positive repayment delay observed during
the six-month period is represented by `max_delay_status`.

| Maximum Delay Status | Score |
|---|---:|
| 0 | 0 |
| 1 | 1 |
| 2 | 2 |
| 3 or greater | 3 |

Higher repayment delay severity was generally associated
with higher historical default rates.

---

## 5. Latest Utilization Score

Latest utilization is calculated as:

latest bill amount / credit limit

| Latest Utilization | Score |
|---|---:|
| Below 50% | 0 |
| 50% to below 70% | 1 |
| 70% to 100% | 2 |
| Above 100% | 3 |

Negative utilization receives zero utilization-risk points.

---

## 6. Payment Behaviour Score

For customers with a positive six-month total bill amount:

payment-to-bill ratio =
total six-month payments / total six-month bill amount

| Payment-to-Bill Ratio | Score |
|---|---:|
| 50% or greater | 0 |
| 20% to below 50% | 1 |
| Below 20% | 2 |

When the six-month total bill amount is zero or negative,
the ratio is treated as not applicable and zero risk points
are assigned for this indicator.

---

## 7. Total Risk Score

The four component scores are added together.

Maximum possible score = 11.

| Total Score | Risk Band |
|---|---|
| 0-2 | LOW |
| 3-5 | MEDIUM |
| 6-11 | HIGH |

---

## 8. Historical Validation

The rule-based classification was evaluated across all
30,000 customers.

| Risk Band | Customers | Historical Defaults | Historical Default Rate |
|---|---:|---:|---:|
| LOW | 13,966 | 1,761 | 12.61% |
| MEDIUM | 9,673 | 1,608 | 16.62% |
| HIGH | 6,361 | 3,267 | 51.36% |

Overall historical default rate: 22.12%.

The observed ordering was:

LOW < MEDIUM < HIGH

The HIGH-risk group represented approximately 21.20% of
customers and contained approximately 49.23% of all
historical defaults.

This validation supports the use of the rules as a
transparent customer-prioritization mechanism.

---

## 9. Important Interpretation

`risk_band` represents the application's rule-based
assessment of behavioural credit risk.

`default_next_month` represents the historical observed
outcome contained in the source dataset.

They are intentionally kept separate.

The risk classification is intended for analytical
prioritization and should not be interpreted as a
machine-learning prediction or automated lending decision.