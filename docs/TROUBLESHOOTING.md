# Troubleshooting

## Strict Verification Fails

Use the original frozen Spec and freeze SHA. Confirm that the formal public directory has 240 task JSON files, `inventory.json`, and `completion.json`. Do not regenerate final records or edit the formal output.

## Aggregate Cannot Rebuild The Plan

Pass `--plan-root` pointing to the read-only frozen checkout that has the locally processed task data. The aggregate output directory may be separate from that checkout.

## Delivery Audit Fails

Read the reported file and remove the offending generated artifact. Typical causes are a copied absolute path, credential-shaped text, or a forbidden field in input aggregate JSON. Rebuild from clean public aggregate inputs rather than editing `data.json` by hand.

## Pytest Collects Historical Run Tests

Use the supported command `python3 -m pytest tests/`. A bare `pytest` may collect generated tests under ignored `runs/` directories, which are not repository tests.
