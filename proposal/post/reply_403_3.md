@JongilHan66 Not quite, my wording was unclear. Keep your form and change two things: multiply `K` at each face by `dp` there, and divide by `dp(i)`:

```
current:  dq/dt(i) = 1/dx(i)         [K(i+.5)          (q(i+1)-q(i))/dx(i+.5) - K(i-.5)          (q(i)-q(i-1))/dx(i-.5)]
proposed: dq/dt(i) = 1/(dp(i) dx(i)) [K(i+.5) dp(i+.5) (q(i+1)-q(i))/dx(i+.5) - K(i-.5) dp(i-.5) (q(i)-q(i-1))/dx(i-.5)]
```

with `dp(i+.5) = (dp(i)+dp(i+1))/2`. Multiplying by `dp(i) dx(i)` and summing over `i`, each face term appears once with each sign, so `Σ q dp dx` is conserved exactly; a uniform `q` still gets zero. Diffusing `q dp` would give a uniform `q` a tendency where `dp` varies. The same applies to T.
