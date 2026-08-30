# V3 plan (next chat)
1. MORE DATA: add 2026-03/04 monthly zips + 4 more symbols (BNB, DOGE, LINK, ADA)
   via the same mrbiznes-research-data repo workflow.
2. REGIME-AWARE backtest: report per-regime (trend day vs range day via daily ADX)
   — v1/v2 hint entries are fine (WR 65-76%) but chop periods destroy payoff;
   a regime gate may be the final missing edge.
3. Exit study matrix on S4 only (entry confirmed): {pure 2R, 2.5R, 3R}, {1R-partial
   0/50/70}, {ATR trail, UT trail} x {costs on/off}, on train only, single OOS read.
4. If regime-gated S4 reaches OOS expectancy > +0.3R with n>=100: promote to LIVE
   signal engine (XT klines + pretty card + score + admin DM). WR target note:
   per research rules, we report achieved numbers, never tuned-to-target.
5. Channel integration order: admin-DM pilot 2 weeks -> VIP gate -> public card.
