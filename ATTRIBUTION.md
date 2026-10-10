# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下公开项目与行业资料，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 / 资料 | 作者 / 来源 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| claude-skill-registry（`skills/other/drama-creator/SKILL.md`） | majiayu000 | MIT（2026-10-11 经 `gh repo view` 核验） | https://github.com/majiayu000/claude-skill-registry | 中文短剧创作方法论的高层框架："钩子-反转-再钩子"单集闭环、把全剧看作情绪曲线来控节奏、台词"先给信息再谈别的"、场景用动作而不用形容词来写。**实现与文案全部原创** |
| screen-creative-skills（`drama-creator` 英文版） | gonglingrui | MIT（2026-10-11 经 `gh repo view` 核验） | https://github.com/gonglingrui/screen-creative-skills | 与上一行同一方法论体系的英文表述，佐证了"每集必须压弹簧或放弹簧、没有中间态"的节奏观。**实现与文案全部原创** |
| h3-studio-runpod（`english-short-drama-writer`） | mojojolo | MIT（2026-10-11 经 `gh repo view` 核验） | https://github.com/mojojolo/h3-studio-runpod | 英文竖屏短剧 skill 的高层思路：开场 5 秒内立微冲突、身份反差式爽点结构、按秒计时的内在节奏。**实现与文案全部原创** |
| biz-ai-video-course（`ai-short-drama-director`） | kouzui-huang | 未声明（仓库未见 LICENSE，2026-10-11 实查） | https://github.com/kouzui-huang/biz-ai-video-course | 仅借鉴高层思路：钩子前置 3 秒、按节拍密度排布反转。因许可未声明，**未借鉴其任何文案与代码** |
| 《价值百万的开篇技巧：黄金 3 秒/章、反转卡点、情绪高潮全解析》 | 木子言呱（360doc 专栏） | 公开文章（非代码/skill 许可） | http://www.360doc.com/content/25/1222/00/80573689_1167090311.shtml | 行业常识层面：前三集"留人/入戏/期待"三板斧、高潮前置、心理 OS 转动作。仅吸收行业常识，**未复制原文** |
| 《下沉短剧写作技巧》《短剧——黄金一分钟》 | 野猫短篇资料库（360doc 专栏） | 公开文章（非代码/skill 许可） | http://www.360doc.com/content/26/0113/12/35955633_1168341390.shtml | 行业常识层面：3 集一个小闭环、每集结尾卡点留钩子、"情绪→情感→期待"三段式开场。仅吸收行业常识，**未复制原文** |

## 未借鉴项（如实标注）

- `jimwoocory/us-vertical-drama-studio`（美剧竖屏 Episode Architect，做节拍表不写剧本）：调研中发现，其许可未及核验，**本插件未借鉴**。
- 上述中文专栏文章的具体案例台词与段落：**均未复制**，本插件的示例剧本、钩子库例句均为原创撰写。
- 短剧行业的"通用剧作常识"（如三幕式、每集 1–2 分钟体量）：属公共领域创作常识，不归属任何一方。

## 声明

1. **借鉴思路，实现与文案均为原创**：以上来源的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则、命令流程、hook 脚本、示例剧本均为独立撰写。
2. **许可合规**：MIT 许可的项目允许在保留声明的前提下进行思路借鉴与二次创作，本文件即为保留声明的一部分；许可未声明的项目仅借鉴高层思路，未复制任何表达。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。
4. **未核实项**：各仓库的 star 数、下载量等热度数据未做核验，本文件与 README 不引用任何热度数字。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
