import glob
import os
from datetime import datetime
from datetime import timezone


def generate_singbox_domains(domains: list[str]) -> str:
    return "\n".join(domains)


def generate_autoproxy_domains(domains: list[str]) -> str:
    # Формат AutoProxy требует специального заголовка
    output_content: str = (
        f"[AutoProxy 0.2.9]\n! generated at {datetime.now(timezone.utc)}\n\n"
    )

    # Добавляем домены.
    # Префикс || означает "сам домен и все поддомены"
    for domain in domains:
        output_content += f"||{domain}\n"
    return output_content


def generate():
    domains = set()

    files = sorted(glob.glob("data/vpn-domains-*.txt"))
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                domain = line.strip()
                if not domain or domain.startswith("#"):
                    continue
                if domain.startswith("!"):
                    excluded = domain[1:].strip()
                    if excluded:
                        domains.discard(excluded)
                else:
                    domains.add(domain)

    domains: list[str] = sorted(domains)  # отсортированный список уникальных доменов
    files_contents: dict[str, str] = (
        {  # имена файлов и их содержимое, в различных форматах
            "data/lists/AutoProxy-vpn-domains.list": generate_autoproxy_domains(
                domains
            ),
            "data/lists/singbox-vpn-domains.list": generate_singbox_domains(domains),
        }
    )

    # Сохраняем в файлы
    for output_path, output_content in files_contents.items():
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)


if __name__ == "__main__":
    generate()
