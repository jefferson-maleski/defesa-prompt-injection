# defesa-prompt-injection

> **Defesa em profundidade contra prompt injection quando agentes de IA leem documentos de partes adversas.**

🇺🇸 **English version: [README.md](README.md)**

Uma skill para Claude Code / Agent SDK projetada para ser invocada como **primeiro passo** antes de qualquer análise de documentos vindos de fontes não confiáveis — peças de parte contrária, contratos de terceiros, e-mails externos, conteúdo extraído de scraping, ou qualquer documento que não tenha sido produzido pela organização do próprio usuário.

[![Skills.sh](https://img.shields.io/badge/skills.sh-listed-blue)](https://skills.sh/jefferson-maleski/defesa-prompt-injection)
[![Licença: Apache 2.0](https://img.shields.io/badge/Licen%C3%A7a-Apache_2.0-blue.svg)](LICENSE)
[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.2.0-green.svg)](CHANGELOG.md)

---

## Por que existe

O OWASP Top 10 para Aplicações Agênticas (2026) classifica prompt injection como o **risco de segurança #1** para agentes de IA. Quando um agente lê um documento produzido por um adversário — a contestação de um banco em ação de fraude consumerista, um contrato de fornecedor de uma contraparte — esse documento pode conter instruções ocultas projetadas para manipular o comportamento do agente.

Esta skill garante que cada byte dentro de um documento adversarial seja tratado como **dado a ser analisado**, nunca como **comando a ser obedecido**.

**Casos de uso**:
- Advocacia: leitura de peças da parte contrária, contestações, recursos, laudos periciais
- Análise contratual: minutas de terceiros, contratos de fornecedores, NDAs de contrapartes
- Due diligence: documentos externos em data rooms
- Pesquisa: artigos, papers ou conteúdo extraído de fontes não confiáveis
- Triagem de e-mail: mensagens com anexos vindas de remetentes externos

## O que faz

A skill define um **protocolo defensivo de 6 passos** que o agente segue antes de ler um documento adversarial:

1. **Anuncia** o arquivo como adversarial — explicitando o modo do agente
2. **Extrai texto bruto** sem normalização via OCR
3. **Inspeção estrutural** — executa [`scripts/detector.py`](scripts/detector.py) (obrigatório desde a v1.2.0) para checar metadados, scripts embutidos, formulários, camadas, texto invisível e coordenadas fora da página
4. **Checklist de padrões** — texto invisível, caracteres de largura zero, frases-gatilho, anotações ocultas (ver [padroes.md](padroes.md))
5. **Análise endurecida** — realiza a análise de domínio ciente de que todo conteúdo interno é adversarial
6. **Relatório estruturado** — em formato tabular obrigatório, expondo ao usuário cada padrão detectado

## O que detecta

| Vetor | Exemplos |
|---|---|
| Texto invisível | Branco sobre branco, fonte ≤ 1pt, opacidade 0 |
| **Texto fora da área visível** | Caracteres desenhados fora do MediaBox (coordenadas negativas, além da margem da página) |
| Caracteres de largura zero | U+200B, U+200C, U+200D, U+FEFF, U+2060, U+202E (inversão RTL) |
| Frases-gatilho | "ignore previous instructions", "you are now", "ATTENTION AI" (inglês) + variantes em português |
| Metadados de PDF | Author/Creator/Producer suspeitos, JavaScript embutido, AcroForm, camadas opcionais |
| Anotações ocultas | Comentários `/Annot`, `/FreeText`, `/Popup`, `/Watermark` |
| Engenharia social | Urgência falsa, inversão de papel, jurisprudência fabricada, falsos "fatos consolidados" |
| Vetores raros | Unicode tag chars (U+E0000–U+E007F), homóglifos, substituição de fonte, esteganografia JBIG2 |

Catálogo completo de padrões: [`padroes.md`](padroes.md).

Cobertura bilíngue: **inglês + português** (com vocabulário jurídico brasileiro).

## Instalação

### Via npx skills (recomendado)

```bash
npx skills add jefferson-maleski/defesa-prompt-injection -g -y
```

### Instalação manual

Clone o repositório no diretório de skills:

**Claude Code (global / nível do usuário)**:
```bash
git clone https://github.com/jefferson-maleski/defesa-prompt-injection ~/.claude/skills/defesa-prompt-injection
```

**Nível de projeto**:
```bash
git clone https://github.com/jefferson-maleski/defesa-prompt-injection .claude/skills/defesa-prompt-injection
```

A skill é detectada automaticamente pelo Claude Code nesses caminhos.

## Uso

A skill se auto-ativa com base nos triggers da descrição. Para forçar invocação explícita:

> "Antes de ler [PDF], roda a defesa-prompt-injection"

> "Run defesa-prompt-injection before reading the opposing party's brief"

O agente vai anunciar a fonte adversarial, inspecionar o arquivo estruturalmente (via `detector.py`), aplicar o checklist de padrões, reportar os achados no formato tabular obrigatório, e prosseguir com a análise de domínio tratando todo texto interno como dado.

### Integração com outras skills

Esta skill **precede** e **complementa**, nunca substitui, suas skills de análise de domínio:

```
Entrada do usuário → defesa-prompt-injection → skill de domínio (análise jurídica, revisão contratual, etc.)
```

Bons exemplos de encadeamento:
- `defesa-prompt-injection` → skill de análise jurídica
- `defesa-prompt-injection` → red-team verifier (entrada + saída verificadas)
- `defesa-prompt-injection` → revisão tabular (executada em cada documento adversarial do lote)

## Obrigatório: script detector em Python

Desde a v1.2.0, a skill obriga a execução de [`scripts/detector.py`](scripts/detector.py) durante o passo 3. O detector aplica o catálogo de padrões de forma programática porque os extratores de PDF do lado do LLM cortam o texto pelo MediaBox — ou seja, o modelo nunca enxerga injeções fora da página, e não há como detectar o que o extrator nunca entrega.

```bash
pip install pdfplumber pypdf pikepdf
python scripts/detector.py caminho/para/suspeito.pdf
```

A saída é agrupada por bloco contíguo (não por caractere) com status (APPROVED / SUSPICIOUS / BLOCKED), contagem de caracteres, coordenadas e amostras de 180 caracteres por achado.

Fixtures de teste com cinco vetores de injeção cada (em português e inglês) estão disponíveis em [`examples/`](examples/) para verificação.

## Limitações

Isto é **defesa em profundidade**, não garantia absoluta. Vetores ainda não cobertos pelo detector automático:
- **Opacidade 0 (alpha=0)** — o `pdfplumber` expõe a cor mas não o alpha do graphics state; verifique manualmente inspecionando o content stream
- Fontes com codificação personalizada que mapeiam glifos para Unicode enganoso (ataque de substituição de fonte)
- Esteganografia avançada em imagens
- Ataques side-channel via timing ou consumo de recursos

Para esses casos, **o filtro final é sempre a revisão humana**. Use esta skill para elevar o piso, não como teto.

## Contribuindo

Novos vetores de ataque são descobertos regularmente. Contribuições são bem-vindas:

1. Abra uma issue descrevendo o vetor com um exemplo reprodutível mínimo
2. Envie um PR adicionando o padrão a [`padroes.md`](padroes.md)
3. Se o vetor for detectável programaticamente, adicione a lógica correspondente em [`scripts/detector.py`](scripts/detector.py)

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para as diretrizes completas.

## Autor

**Jefferson Maleski** — [@jefferson-maleski](https://github.com/jefferson-maleski)

## Construído com

Desenvolvido com auxílio do [Claude](https://www.anthropic.com/claude) (Sonnet 4.6) via [Claude Code](https://www.anthropic.com/claude-code).

## Licença

Apache License 2.0 — texto completo em [LICENSE](LICENSE).

## Aviso

Esta skill é fornecida "no estado em que se encontra", sem garantia de qualquer espécie. É um auxílio defensivo, não um substituto para o julgamento humano. O autor e os contribuidores não se responsabilizam por danos decorrentes do uso, mau uso ou falha desta skill. Sempre combine com revisão humana em decisões de alto impacto.
