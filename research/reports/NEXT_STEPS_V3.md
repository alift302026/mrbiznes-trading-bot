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

## V3 results (2026-08-31) + FINAL shipped engine
Regime gate + exit matrix on S4: NO OOS rescue (agg n=62, WR 51.6%, EXP -1.49R).
Verdict: the honest finding stands — 15m entries ~65-76% directional WR across
4 majors (May-Jul 2026), but payoff < costs in chop. Profitability is NOT
claimed anywhere in product copy.
FINAL shipped (this commit): production S4 engine in app/engines/signals/
final_setup_engine.py (validated classic params: 40-bar level, retest, body>=60%,
relvol>=1.2, SL=extreme+0.5ATR, TP1=1R/TP2=2R/TP3=3R display, UT Bot confirm,
4H/1H/15m pipeline, 0-100 confluence score, A+ >= 85), hourly worker
(final_signal_worker, paper mode flag FINAL_SIGNALS_PUSH, default 0),
admin preview command /signalpreview (renders the SAME signal-section card).
Sample: ETHUSDT SHORT 2026-07-31 12:30 UTC, score 94, A+ (see samples/).
Next: (a) 2-week paper forward-validation via worker store, (b) forward WR/PF
report, (c) VIP gate + push, (d) LiquiditySweep+FVG research branch.
