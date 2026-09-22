# Status e próximos passos — Certidões automatizadas

> Auditoria de 22/09/2026. Esta é uma fotografia baseada em arquivos, Git, artefatos e endpoints observáveis. Nenhum build completo foi executado nesta classificação.

## Classificação

- **Estado:** protótipo pausado e versionado
- **Confiança:** alta
- **Natureza:** automação Python de portais públicos

## Evidências observadas

- O repositório está limpo e o último commit local é de abril de 2026.
- Há módulos por portal, Streamlit, CLI e OCR experimental.
- O README local ainda faz promessas de robustez e automação total que não foram validadas.

## Diagnóstico franco

Pode ser retomado como assistente de consulta, nunca como emissor garantido nem como ferramenta de contorno de CAPTCHA.

## Upgrades previstos

### P0 — preservar e tornar retomável

- Sincronizar e revisar o README remoto mais sóbrio antes de trabalhar.
- Testar um portal por vez, respeitando termos e interação humana.
- Inventariar mudanças de formulário e dependências.

### P1 — estabilizar

- Criar contratos de resultado, timeouts, screenshots de erro e testes com páginas simuladas.
- Tratar CAPTCHA como ponto de parada/manual quando exigido.
- Proteger e apagar certidões/dados pessoais conforme política definida.

### P2 — evoluir

- Integrar somente fontes estáveis e autorizadas a uma fila auditável.

## Critério para considerar retomado

O projeto será considerado retomado quando um portal suportado funcionar de forma assistida, auditável e conforme as regras, sem alegação de garantia.

## Prompt de retomada para o Codex

> Retome o projeto **Certidões automatizadas** nesta pasta. Leia este arquivo e o README, inspecione o Git e preserve todo trabalho local. Comece somente pelo P0, valide com evidências e não implemente P1/P2 antes de apresentar o diagnóstico atualizado.

