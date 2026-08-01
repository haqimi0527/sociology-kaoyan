# -*- coding: utf-8 -*-
"""AI 语义近义检测：DeepSeek 分批审查全部概念，找"概念名不同但实质同一考点"的组

按 chapter 顶层分域（理论/方法/概论/其他），每批 ~120 条，调 DeepSeek 找近义组。
输出 D:/workspace/_ai_semantic_merge.json
"""
import json, io, sys, time, re, urllib.request
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT = "D:/workspace/_ai_semantic_merge.json"
KEY = open("D:/workspace/.deepseek_key", encoding='utf-8').read().strip()
API = "https://api.deepseek.com/chat/completions"

def call_deepseek(prompt, retries=2):
    req = urllib.request.Request(API,
        data=json.dumps({"model": "deepseek-chat",
                         "messages": [{"role": "user", "content": prompt}],
                         "max_tokens": 1500, "temperature": 0}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    for attempt in range(retries + 1):
        try:
            resp = json.load(urllib.request.urlopen(req, timeout=120))
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == retries:
                return f"__ERROR__: {e}"
            time.sleep(3)

def parse_json(content):
    if content.startswith("__ERROR__"):
        return None, content
    m = re.search(r'\[.*\]', content, re.DOTALL)
    if not m:
        return None, f"无JSON: {content[:100]}"
    try:
        return json.loads(m.group(0)), None
    except Exception as e:
        return None, f"JSON解析失败: {e}"

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    domains = defaultdict(list)
    for c in cs:
        top = (c.get('chapter') or '').split('/')[0] or '其他'
        domains[top].append(c)
    print(f"域分布: { {k: len(v) for k, v in domains.items()} }")

    all_cand = []
    errors = []
    for domain, items in domains.items():
        for i in range(0, len(items), 120):
            batch = items[i:i+120]
            lines = [f"{c['term']}|{(c.get('definition') or '')[:40]}" for c in batch]
            prompt = (
                f"以下是社会学考研概念库「{domain}」域的部分概念（格式: 概念名|定义摘要）。\n"
                f"请找出所有『概念名不同但实质指同一个考点/同一个概念』的组。\n"
                f"例如: 模式变量/模式变项 是同一概念; 理性化/合理化 可能是同一概念。\n"
                f"严格要求: 只找实质同一的变体/译名/别名; 子概念、父子概念、不同概念绝不要列。\n"
                f"输出 JSON 数组, 每项 {{\"terms\":[\"概念名A\",\"概念名B\"],\"reason\":\"为什么同一\"}}。\n"
                f"没有可合并的则输出 []。\n\n概念列表:\n" + "\n".join(lines)
            )
            content = call_deepseek(prompt)
            parsed, err = parse_json(content)
            if parsed:
                # 只保留 term 都在当前批次里的
                valid = [g for g in parsed if isinstance(g, dict) and len(g.get('terms', [])) >= 2]
                for g in valid:
                    g['domain'] = domain
                    g['batch_terms'] = [c['term'] for c in batch]
                all_cand.extend(valid)
                print(f"[{domain} {i//120+1}] 发现 {len(valid)} 组")
            else:
                errors.append(f"{domain}/{i}: {err}")
            time.sleep(1)

    json.dump({"candidates": all_cand, "errors": errors},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n共发现近义候选组: {len(all_cand)}")
    print(f"错误: {len(errors)}")
    for g in all_cand:
        print(f"  {g['terms']} | {g.get('reason','')[:40]}")
    print(f"→ {OUT}")
    if errors:
        print("\n错误明细:")
        for e in errors[:10]:
            print(f"  {e}")

if __name__ == '__main__':
    main()
