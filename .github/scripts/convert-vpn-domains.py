import glob
import os
from datetime import datetime
from datetime import timezone


def _normalize_for_match(value: str) -> str:
    # нижний регистр + без лидирующих точек: ".ua" и "ua" — одно и то же
    return value.strip().lower().lstrip(".")


def _matches_exclusion(domain: str, pattern: str) -> bool:
    """True, если domain покрывается исключением pattern.

    '!example.com' удаляет 'example.com', 'www.example.com',
    но не 'badexample.com'. '!ua' удаляет 'example.ua' и т.д.
    """
    d = _normalize_for_match(domain)
    p = _normalize_for_match(pattern)
    if not p:
        return False
    return d == p or d.endswith("." + p)


def _strip_inline_comment(line: str) -> str:
    # Всё, что после '#', — комментарий (и полная строка, и конец строки)
    return line.split("#", 1)[0].strip()


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

    # Файлы обрабатываются последовательно по алфавиту.
    # Исключение '!foo' в файле N удаляет из накопления (файлы 1..N-1
    # и более ранние строки файла N) сам 'foo' и все его поддомены,
    # но не мешает снова добавить их в файлах N+1, N+2, ...
    files = sorted(glob.glob("data/vpn-domains-*.txt"))
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                token = _strip_inline_comment(line)
                if not token:
                    continue
                if token.startswith("!"):
                    rest = token[1:].strip()
                    if not rest:
                        continue
                    # первое слово после '!' — шаблон исключения
                    excluded = rest.split()[0]
                    if not excluded:
                        continue
                    # удаляем сам домен и все поддомены:
                    # '!example.com' -> 'example.com', 'www.example.com',
                    # но не 'badexample.com'. '!ua' -> все '*.ua'.
                    to_remove = [
                        d for d in domains if _matches_exclusion(d, excluded)
                    ]
                    for d in to_remove:
                        domains.discard(d)
                else:
                    # первое слово — домен, остаток строки игнорируем
                    domain = token.split()[0]
                    if domain:
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
