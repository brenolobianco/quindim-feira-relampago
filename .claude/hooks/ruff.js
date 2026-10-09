const { spawnSync } = require("node:child_process");
const path = require("node:path");

let entrada = "";
process.stdin.on("data", (pedaco) => (entrada += pedaco));
process.stdin.on("end", () => {
  const arquivo = JSON.parse(entrada).tool_input?.file_path ?? "";
  if (!arquivo.endsWith(".py")) return;

  const opcoes = { cwd: path.dirname(arquivo), stdio: "ignore" };
  const formatar = spawnSync("uv", ["run", "--quiet", "ruff", "format", arquivo], opcoes);
  if (formatar.error) {
    console.error(`uv não encontrado no PATH do Claude Code: ${arquivo} não foi formatado nem checado.`);
    process.exit(2);
  }
  spawnSync("uv", ["run", "--quiet", "ruff", "check", "--fix", "--unfixable", "F401", arquivo], opcoes);

  const checagem = spawnSync("uv", ["run", "--quiet", "python", path.join(__dirname, "comentarios.py"), arquivo], {
    cwd: opcoes.cwd,
    encoding: "utf8",
    env: { ...process.env, PYTHONUTF8: "1" },
  });
  if (checagem.status !== 0) {
    console.error(`Não consegui checar comentários em ${arquivo}:\n${checagem.stderr}`);
    process.exit(2);
  }
  if (checagem.stdout.trim()) {
    console.error(`Comentário é proibido neste projeto (CLAUDE.md). Remova de ${arquivo}:\n${checagem.stdout}`);
    process.exit(2);
  }
});
