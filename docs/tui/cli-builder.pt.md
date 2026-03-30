# Construtor de CLI

O `nbx cli tui` lança um construtor de comandos interativo que permite navegar a
árvore da CLI visualmente, montar um comando, executá-lo e inspecionar o resultado
sem sair do terminal.

## Lançamento

```bash
nbx cli tui
nbx demo cli tui
```

## Para que serve

- aprender a árvore de comandos sem memorizar cada ramo
- montar comandos dinâmicos longos passo a passo
- testar invocações `nbx` antes de copiá-las para scripts ou histórico do shell
- explorar a mesma árvore contra seu perfil default ou demo

## Notas

- O construtor executa comandos `nbx` reais.
- Complementa, em vez de substituir, a documentação CLI padrão em
  [CLI](../cli/index.md).
- O tratamento de tema segue o mesmo catálogo de temas TUI integrado das outras
  aplicações Textual.

## Capturas de tela

- [Galeria do construtor de CLI](screenshots-cli.md)
