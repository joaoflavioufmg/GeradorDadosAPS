"""
Orquestra geração de .dat (opcional) e execução AMPL+Gurobi com caminhos escolhidos.

Uso:
  # Só otimizar com .dat existentes:
  python step_v2.py --municipio "Lagoa Santa" --dat "C:\\aps\\Lagoa Santa.dat" --dat-dist "C:\\aps\\Lagoa Santa_distance.dat"

  # Gerar .dat e otimizar (ficheiros em Dados/<municipio>/dados_brutos/):
  python step_v2.py --municipio "Lagoa Santa" --gerar

  # Outro município (obrigatório --candidatos-xlsx para locais candidatos):
  python step_v2.py --municipio "Contagem" --gerar --candidatos-xlsx "C:\\aps\\data\\candidatos.xlsx"

  # Só gerar dados, sem AMPL:
  python step_v2.py --municipio "Lagoa Santa" --gerar --no-ampl
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
from create_dat_files import CreatorDatFiles

# Raiz GeraDadosAPS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "Dados")
# Repositório APS (pasta pai de GeraDadosAPS)
REPO_ROOT = Path(BASE_DIR).resolve().parent

# Igual ao otimiza_ampl.bat: linhas 1–1242 do aps.mod (índice 0 .. 1241); cauda do aps.run a partir da linha 22
_MOD_DECL_LINE_COUNT = 1242
_RUN_TAIL_START_INDEX = 21
_DEFAULT_AMPL_HOME = Path(r"C:\Solvers\AMPL")


def _pastas(municipio: str) -> dict:
    return {
        "todos_municipios": os.path.join(DADOS_DIR, "Dados_todos_municipios"),
        municipio: os.path.join(DADOS_DIR, f"{municipio}/dados_brutos"),
    }


def _default_candidatos_path(municipio: str) -> str | None:
    if municipio.strip().lower() == "lagoa santa":
        return r"C:\aps\data\selecao_candidatos_final_lagoa_santa.xlsx"
    return None


def build_scenario(
    municipio: str,
    candidatos_xlsx: str | None = None,
    tipo_dos_dados: ExecutionDataType = ExecutionDataType.BY_CLUSTER,
) -> tuple[ConfigurationDataScenario, PathArquivoDados]:
    """Monta configs e paths como no step.py, com saída em dados_brutos do município."""
    pastas = _pastas(municipio)
    candidatos = candidatos_xlsx or _default_candidatos_path(municipio)
    if not candidatos:
        raise ValueError(
            f"Defina --candidatos-xlsx para o município «{municipio}» (sem preset)."
        )

    dados_setor_censitario_completo = os.path.join(
        pastas["todos_municipios"], "dados_SC_fonte_completa.xlsx"
    )
    out_base = os.path.join(pastas[municipio], municipio)

    configs = ConfigurationDataScenario(
        municipio=municipio,
        budget=19333029.53,
        I_L1=3818078,
        I_L1_exp=1200000,
        raios_criticos={"PHC": 5000, "SHC": 30000, "THC": 35000},
        custos_mensais_PHC={"eSF": 288000, "eSB": 105248, "eMulti": 322625, "ACS": 36280},
        custos_mensais_SHC={"EQ2": 0},
        custos_mensais_THC={"EQ3": 0},
        equipes_saude_primario=["eSF", "eSB", "eMulti", "ACS"],
        equipes_saude_secundario=["EQ2"],
        equipes_saude_terciario=["EQ3"],
        name_output_file=out_base,
        maximo_de_unidades_abertas={"1": 10, "2": 1, "3": 1},
        encaminhamentos_primeiro_nivel={"1": 0.71, "2": 0.20, "3": 0.05},
        encaminhamentos_segundo_nivel={"1": 0.65, "2": 0.20, "3": 0.10},
        encaminhamentos_terceiro_nivel={"1": 0.8, "2": 0.1, "3": 0.05},
        maximo_atendimentos_telemedicina={
            "MAX_TELE_PHC": 0.05,
            "MAX_TELE_SHC": 0.05,
            "MAX_TELE_THC": 0.05,
        },
        maximo_deslocamento={
            "MAX_HOME_PHC": 1,
            "MAX_HOME_SHC": 0.15,
            "MAX_HOME_THC": 0.05,
        },
        name_output_file_distancias=f"Dist_{municipio.replace(' ', '_')}",
        tipo_rodada=tipo_dos_dados,
    )

    paths_arquivos = PathArquivoDados(
        path_arquivo_setores_censitarios=dados_setor_censitario_completo,
        path_dados_IVS=os.path.join(pastas["todos_municipios"], "dados_IVS.xlsx"),
        path_equipes_PHC=os.path.join(pastas[municipio], "v02_Equipe.xlsx"),
        path_setores_com_UBS=os.path.join(pastas["todos_municipios"], "setores_com_ubs.xlsx"),
        path_arquivos_dat_final=pastas[municipio],
        path_cluster_CSV=os.path.join(pastas["todos_municipios"], "sector_cluster_by_uf.csv"),
        path_porte_UBS=os.path.join(pastas["todos_municipios"], "Porte_UBS.xlsx"),
        path_locais_candidatos=candidatos,
        path_dados_custo=os.path.join(
            pastas["todos_municipios"], "Dados_custos_finais_formatados.xlsx"
        ),
    )
    return configs, paths_arquivos


def generate_dat_files(
    municipio: str, candidatos_xlsx: str | None = None, create_distance_file: bool = True
) -> tuple[Path, Path]:
    """Gera «…/<municipio>.dat» e «…/<municipio>_distance.dat» em dados_brutos."""
    configs, paths_arquivos = build_scenario(municipio, candidatos_xlsx)
    creator = CreatorDatFiles(
        configuration_data=configs,
        path_arquivos_data=paths_arquivos,
        create_distance_file=create_distance_file,
    )
    creator.create_file()
    main_dat = Path(configs.name_output_file + ".dat").resolve()
    dist_dat = Path(configs.name_output_file + "_distance.dat").resolve()
    if not main_dat.is_file():
        raise FileNotFoundError(f"Não encontrado após geração: {main_dat}")
    if create_distance_file and not dist_dat.is_file():
        raise FileNotFoundError(f"Não encontrado após geração: {dist_dat}")
    return main_dat, dist_dat


def _ampl_path_for_statement(p: Path) -> str:
    """Caminho absoluto com barras normais, para linhas model/data do AMPL."""
    return str(p.resolve()).replace("\\", "/")


def run_ampl_gurobi(
    dat_file: Path,
    dist_dat_file: Path,
    repo_root: Path | None = None,
    ampl_home: Path | None = None,
) -> int:
    """
    Gera aps_decl_ampl.mod e sessão .run no %TEMP% e executa ampl.exe (mesma lógica que otimiza_ampl.bat).
    """
    repo_root = repo_root or REPO_ROOT
    ampl_home = ampl_home or _DEFAULT_AMPL_HOME
    ampl_exe = ampl_home / "ampl.exe"
    if not ampl_exe.is_file():
        raise FileNotFoundError(f"ampl.exe não encontrado: {ampl_exe}")

    mod_path = repo_root / "aps.mod"
    run_path = repo_root / "aps.run"
    if not mod_path.is_file():
        raise FileNotFoundError(f"aps.mod não encontrado: {mod_path}")
    if not run_path.is_file():
        raise FileNotFoundError(f"aps.run não encontrado: {run_path}")

    import tempfile

    enc = "utf-8"
    mod_text = mod_path.read_text(encoding=enc, errors="replace")
    mod_lines = mod_text.splitlines()
    decl_lines = mod_lines[:_MOD_DECL_LINE_COUNT]
    decl_path = Path(tempfile.gettempdir()) / "aps_decl_ampl.mod"
    decl_path.write_text("\n".join(decl_lines) + "\n", encoding=enc)

    run_lines = run_path.read_text(encoding=enc, errors="replace").splitlines()
    tail_lines = run_lines[_RUN_TAIL_START_INDEX:]

    d1 = _ampl_path_for_statement(dat_file)
    d2 = _ampl_path_for_statement(dist_dat_file)
    decl_s = _ampl_path_for_statement(decl_path)

    head_lines = [
        "reset data;",
        f'model "{decl_s}";',
        f'data "{d1}";',
        f'data "{d2}";',
    ]
    session_text = "\n".join(head_lines + tail_lines) + "\n"
    session_path = Path(tempfile.gettempdir()) / "aps_ampl_session.run"
    session_path.write_text(session_text, encoding=enc)

    env = os.environ.copy()
    env["PATH"] = str(ampl_home) + os.pathsep + env.get("PATH", "")

    proc = subprocess.run(
        [str(ampl_exe), str(session_path)],
        cwd=str(repo_root),
        env=env,
    )
    return int(proc.returncode)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera .dat (opcional) e executa AMPL+Gurobi.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--municipio", required=True, help='Nome do município (ex.: "Lagoa Santa")')
    p.add_argument("--dat", type=Path, help="Ficheiro .dat principal (cenário)")
    p.add_argument("--dat-dist", type=Path, dest="dat_dist", help="Ficheiro .dat de distâncias")
    p.add_argument(
        "--gerar",
        action="store_true",
        help="Gera novos .dat via CreatorDatFiles antes da otimização",
    )
    p.add_argument(
        "--candidatos-xlsx",
        type=str,
        default=None,
        help="Excel de locais candidatos (obrigatório se não houver preset para o município)",
    )
    p.add_argument(
        "--no-distance",
        action="store_true",
        help="Com --gerar: não gera ficheiro _distance.dat (só se souber que não precisa)",
    )
    p.add_argument(
        "--no-ampl",
        action="store_true",
        help="Não executa AMPL (útil só com --gerar)",
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Pasta com aps.mod e aps.run",
    )
    p.add_argument(
        "--ampl-home",
        type=Path,
        default=_DEFAULT_AMPL_HOME,
        help="Pasta da instalação AMPL (com ampl.exe)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.gerar and args.no_distance and not args.no_ampl:
        print(
            "Erro: com --gerar não há segundo .dat de distâncias; use --no-ampl ou não passe --no-distance.",
            file=sys.stderr,
        )
        return 2

    if args.gerar:
        main_dat, dist_dat = generate_dat_files(
            args.municipio,
            candidatos_xlsx=args.candidatos_xlsx,
            create_distance_file=not args.no_distance,
        )
        print(f"Gerado: {main_dat}")
        if not args.no_distance:
            print(f"Gerado: {dist_dat}")
    else:
        if not args.dat or not args.dat_dist:
            print(
                "Erro: sem --gerar é necessário --dat e --dat-dist.",
                file=sys.stderr,
            )
            return 2
        main_dat = args.dat.resolve()
        dist_dat = args.dat_dist.resolve()
        if not main_dat.is_file():
            print(f"Erro: não existe --dat: {main_dat}", file=sys.stderr)
            return 2
        if not dist_dat.is_file():
            print(f"Erro: não existe --dat-dist: {dist_dat}", file=sys.stderr)
            return 2

    if args.no_ampl:
        print("Pular AMPL (--no-ampl).")
        return 0

    print("Executando AMPL+Gurobi…")
    code = run_ampl_gurobi(
        main_dat,
        dist_dat,
        repo_root=args.repo_root.resolve(),
        ampl_home=args.ampl_home,
    )
    if code != 0:
        print(f"AMPL terminou com código {code}.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())



"""
cd C:\aps\GeraDadosAPS

# Já tens .dat na raiz do repo
python step_v2.py --municipio "Lagoa Santa" --dat "C:\aps\Lagoa Santa.dat" --dat-dist "C:\aps\Lagoa Santa_distance.dat"

# Gerar + AMPL
python step_v2.py --municipio "Lagoa Santa" --gerar

# Só gerar
python step_v2.py --municipio "Lagoa Santa" --gerar --no-ampl


"""