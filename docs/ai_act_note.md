# EU AI Act classification note (template)

> This is a learning artefact, not legal advice. Verify every statement against the current official text
> of Regulation (EU) 2024/1689 before publishing or relying on it.

## System description
Fraud-scoring model that ranks payment transactions for human review (demonstration only, synthetic data).

## Classification reasoning (fill in and cite article/annex numbers yourself)
1. **Is it an "AI system" under the Act?** [ ] (machine-learning model producing scores that influence review decisions)
2. **Prohibited practices?** [ ] (expected: no; check the list of prohibited uses)
3. **High-risk (Annex III)?** Check the creditworthiness/credit-scoring entry. As far as I know, that entry carves out AI used
   to detect financial fraud. Read the exact wording and note how it applies here: [ ]
4. **Transparency obligations?** [ ] (not a chatbot or generative system; note why)
5. **Voluntary good practice adopted anyway:** model card, explanations per alert, human review of every alert, monitoring plan.

## GDPR pointers (for a real deployment; the demo uses no personal data)
- Lawful basis and purpose limitation for fraud prevention: [ ]
- Automated decision-making: a human reviews every alert, so no decision is fully automated: [ ]
- DPIA likely needed for large-scale profiling: [ ]

## Conclusion
[ one paragraph: your classification, what would change it, and what you would need before a real deployment ]
