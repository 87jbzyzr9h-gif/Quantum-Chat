# Scientific scope and equations

This is an implementation of established superdense coding for education and
reproducible numerical exploration, not a new communication law.

## Conventions

The basis order is A,B: |00>, |01>, |10>, |11>. Prepare

\[
|\Phi^+\rangle=\operatorname{CNOT}_{A\to B}(H_A\otimes I_B)|00\rangle
=(|00\rangle+|11\rangle)/\sqrt 2.
\]

For bits z,x, apply Z^z and then X^x, giving operator X^x Z^z on A. After A
arrives at the receiver, CNOT then H(A) produces

\[
(H_A\otimes I_B)\operatorname{CNOT}_{A\to B}
(X_A^x Z_A^z\otimes I_B)|\Phi^+\rangle=e^{i\theta}|zx\rangle.
\]

The global phase is unobservable. Four orthogonal Bell states are distinguished
jointly. Each transmitted A represents two classical bits with one already-shared
Bell pair, whose distribution is a separate resource. See
[Bennett & Wiesner (1992)](https://doi.org/10.1103/PhysRevLett.69.2881) and
[IBM's protocol](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/superdense-coding).

## Marginal state and no-signalling

For every encoded Bell state,

\[
\rho_B=\operatorname{Tr}_A(|\psi_{zx}\rangle\langle\psi_{zx}|)=I/2.
\]

Therefore P(B=0)=P(B=1)=1/2 independently of z,x. More local samples or a
classifier do not alter that ideal marginal. A must arrive for joint decoding.
Observer amplitudes are not supplied to the logical receiver.
[IBM reduced states](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/multiple-systems).

## Noise and retry

The modeled A-transit channel is

\[
\mathcal E_p(\rho)=(1-p)\rho+\frac p3
(X_A\rho X_A+Y_A\rho Y_A+Z_A\rho Z_A).
\]

The joint decoder returns the correct symbol with probability 1-p and each
other symbol with p/3. An ensemble is generally mixed; exact density matrices
describe it, while qsimcirq one-shot executions provide measured histograms.

For frame length L bytes, m=4L symbols. Assuming independent transit errors,
ideal gates/preparation and negligible checksum collision probability, a whole
unchanged frame has probability (1-p)^m. A 75-byte ACK survives independent
bit error q with probability (1-q)^600. Hence the approximate confirmation
model for R attempts is

\[
s=(1-p)^{4L}(1-q)^{600},\qquad P(\text{confirmed by }R)=1-(1-s)^R.
\]

These equations omit erasure, storage noise, imperfect Bell distribution,
hardware errors, physical latency and adversarial traffic. Varying frame
lengths must not be represented by a single fixed-L benchmark curve.

## Limits of the claims

- Exact recovery decodes information actually sent; it does not infer an arbitrary file from a tiny hint.
- TCP localhost is a classical simulator interface, not a physical quantum link.
- Global-state access is privileged diagnostics, not a local physical measurement.
- A checksum is not encryption or authentication.
- Repeated messages test repeatability, not language-model generalization.
- Finite sample counts do not prove a theorem or guarantee future performance.
- QML, pre-shared-key reconstruction, hardware quantum networking and FTL are outside this release.

Primary references are listed in [references.bib](references.bib).
