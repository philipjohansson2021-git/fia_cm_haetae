---
marp: true
theme: default
size: "16:9"
lang: ko
math: mathjax
paginate: true
header: "Marp 연구 발표 템플릿"
footer: ""
title: "Marp 연구 발표 템플릿"
author: "김박사"
---

<style>
section {
    background: #fdfdff;
    color: #1f2937;
    font-size: 28px;
    line-height: 1.45;
    padding: 60px 80px;
    word-break: keep-all;
    overflow-wrap: break-word;
}

section h1,
section h2 {
    text-align: center;
}

section h1 {
    font-size: 1.8em;
}

section h2 {
    font-size: 1.35em;
}

section pre {
    font-size: 21px;
    line-height: 1.35;
}

section table {
    display: table;
    margin: 0.5em auto;
    max-width: 100%;
    font-size: 0.9em;
}

section img {
    display: block;
    margin: 0 auto;
}

section blockquote {
    margin: 0.7em 0;
    padding-left: 1em;
    border-left: 4px solid #6b7280;
}

header {
    font-size: 16px;
}

section::after {
    content: attr(data-marpit-pagination) " / " attr(data-marpit-pagination-total);
    font-size: 11px;
}

section.lead {
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
}

section.divider h1 {
    padding-bottom: 0.15em;
    border-bottom: 2px solid #374151;
}

section.small {
    font-size: 22px;
}

section.code-small pre {
    font-size: 18px;
}

section.tiny {
    font-size: 18px;
}

section.code-tiny pre {
    font-size: 14px;
}

.columns {
    display: flex;
    gap: 48px;
    align-items: flex-start;
}

.column {
    flex: 1;
    min-width: 0;
}

.takeaway {
    margin: 0.7em 0;
    padding: 0.55em 1em;
    border: 1px solid #9ca3af;
    border-left: 6px solid #1f3a8a;
    background: #f5f7ff;
    font-weight: 700;
    text-align: center;
}

.references {
    font-size: 0.78em;
    line-height: 1.45;
}

.contact {
    font-size: 0.85em;
    text-align: center;
}

section.lead header,
section.lead footer,
section.lead::after {
    display: none;
}
</style>

<!-- _class: lead -->

<!-- 강제 줄 바꿈에는 </br>를 사용합니다. -->

# 연구 발표 템플릿 </br> with Marp

### 수식 · 알고리즘 · C/Python 코드 중심

**발표자:** 김박사  
**날짜:** 2026년 7월 22일

---

## 목차 (Contents)

<!-- 실제 발표에서는 섹션 구성에 맞게 수정하세요. -->

1. 기본 Markdown과 발표 구성
2. 수학 공식·수식·기호
3. 알고리즘과 의사코드
4. C와 Python 코드
5. 레이아웃과 마무리

---

<!-- _class: lead divider -->
# 1부 · 기본 Markdown과 발표 구성

---

## 템플릿 철학

이 템플릿은 **Markdown과 최소한의 CSS**만 사용합니다.

* 내용과 논리 구조에 먼저 집중합니다.
* 한 슬라이드에는 하나의 핵심 메시지만 담습니다.
* 복잡한 장식보다 읽기 쉬운 수식과 코드를 우선합니다.

> **Simplicity is the ultimate sophistication.**

---

## Markdown 파일에 주석 달기

아래 HTML 주석은 발표 자료에 표시되지 않습니다.

```markdown
<!--
발표자 메모, 수정 예정 내용, 출처 확인 사항 등을 적습니다.
-->
```

<!--
이 주석은 실제 슬라이드에 표시되지 않습니다.
-->

---

## 텍스트 강조와 목록

* **굵게:** 핵심 주장이나 결론
* *기울임:* 용어, 변수, 책·논문 제목
* `인라인 코드`: 함수명, 명령어, 파일명
* ~~취소선~~: 폐기된 가설이나 이전 값

1. 문제를 정의합니다.
2. 방법을 설명합니다.
3. 결과를 제시합니다.
4. 결론과 한계를 정리합니다.

---

## 표 (Tables)

| 모델 | 정확도 | 추론 시간 | 비고 |
|:---:|---:|---:|:---|
| Model A | 92.5% | 12 ms | 기준 모델 |
| Model B | **95.1%** | 15 ms | 제안 모델 |

정렬 표시는 다음과 같습니다.

* `:---:` 가운데 정렬
* `---:` 오른쪽 정렬
* `:---` 또는 `---` 왼쪽 정렬

---

## 이미지 삽입

Marp는 Markdown 이미지 문법에 크기 지정 문법을 더해 사용할 수 있습니다.

```markdown
![h:420](images/이미지_삽입_데모.png "실험 결과 이미지 예시")
```

![h:380](images/이미지_삽입_데모.png "이미지 설명 문구")

---

## 인용문 (Blockquote)

> 인용문은 연구 배경, 문제 정의, 핵심 관찰을 강조할 때 유용합니다.  
> 출처가 있다면 같은 슬라이드나 참고문헌에 함께 표시합니다.

중첩 인용도 사용할 수 있습니다.

> 첫 번째 수준의 인용문
>
> > 두 번째 수준의 인용문

---

<!-- _class: lead divider -->
# 2부 · 수학 공식·수식·기호

---

## 수식 입력의 기본

프론트매터의 `math: mathjax`를 사용합니다.

인라인 수식은 `$...$`로 작성합니다.

* 질량–에너지 등가 원리: $E = mc^2$
* 유클리드 거리: $d(\mathbf{x},\mathbf{y}) = \lVert \mathbf{x}-\mathbf{y} \rVert_2$

블록 수식은 `$$...$$`로 작성합니다.

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

---

## 여러 줄 수식 정렬

등호나 연산자를 기준으로 정렬하면 유도 과정을 읽기 쉽습니다.

$$
\begin{aligned}
f(x) &= ax^2 + bx + c, \\
f'(x) &= 2ax + b, \\
f''(x) &= 2a.
\end{aligned}
$$

한 줄에 한 단계만 두고, 중요한 변형 이유는 본문에서 설명합니다.

---

## 조건별 정의 (Cases)

구간이나 조건에 따라 값이 달라지는 함수는 `cases`를 사용합니다.

$$
\operatorname{ReLU}(x) =
\begin{cases}
0, & x < 0, \\
x, & x \ge 0.
\end{cases}
$$

확률질량함수 예시:

$$
P(X=x) =
\begin{cases}
p, & x=1, \\
1-p, & x=0, \\
0, & \text{otherwise}.
\end{cases}
$$

---

## 벡터와 행렬

$$
\mathbf{x} =
\begin{bmatrix}
x_1 \\
x_2 \\
\vdots \\
x_n
\end{bmatrix},
\qquad
\mathbf{A} =
\begin{bmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{bmatrix}
$$

행렬–벡터 곱:

$$
\mathbf{y} = \mathbf{A}\mathbf{x},
\qquad
y_i = \sum_{j=1}^{n} a_{ij}x_j.
$$

---

## 합·곱·적분·극한

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2},
\qquad
\prod_{i=1}^{n} x_i
$$

$$
\int_a^b f(x)\,dx,
\qquad
\lim_{x \to 0} \frac{\sin x}{x} = 1
$$

$$
\nabla_{\boldsymbol{\theta}} L(\boldsymbol{\theta})
=
\begin{bmatrix}
\frac{\partial L}{\partial \theta_1} &
\cdots &
\frac{\partial L}{\partial \theta_d}
\end{bmatrix}^{\!T}
$$

---

## 확률과 통계

기댓값과 분산:

$$
\mathbb{E}[X] = \sum_x xP(X=x),
\qquad
\operatorname{Var}(X) = \mathbb{E}[(X-\mu)^2].
$$

정규분포:

$$
f(x) = \frac{1}{\sqrt{2\pi\sigma^2}}
\exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right).
$$

조건부확률과 베이즈 정리:

$$
P(A\mid B)=\frac{P(B\mid A)P(A)}{P(B)}.
$$

---

<!-- _class: small -->
## 자주 쓰는 수학 기호

| 용도 | 입력 | 표시 |
|---|---|---|
| 실수·정수 집합 | `\mathbb{R}`, `\mathbb{Z}` | $\mathbb{R},\ \mathbb{Z}$ |
| 벡터·행렬 | `\mathbf{x}`, `\mathbf{A}` | $\mathbf{x},\ \mathbf{A}$ |
| 원소·부분집합 | `\in`, `\subseteq` | $x\in A,\ A\subseteq B$ |
| 합집합·교집합 | `\cup`, `\cap` | $A\cup B,\ A\cap B$ |
| 모든·존재 | `\forall`, `\exists` | $\forall x,\ \exists y$ |
| 함의·동치 | `\Rightarrow`, `\Leftrightarrow` | $P\Rightarrow Q,\ P\Leftrightarrow Q$ |
| 근사·비례 | `\approx`, `\propto` | $a\approx b,\ y\propto x$ |
| 노름·내적 | `\lVert x\rVert`, `\langle x,y\rangle` | $\lVert x\rVert,\ \langle x,y\rangle$ |

그리스 문자 예시: $\alpha,\beta,\gamma,\delta,\epsilon,\theta,\lambda,\mu,\sigma,\phi,\omega$

---

## 수식에 번호와 설명 붙이기

$$
L(\boldsymbol{\theta})
= \frac{1}{N}\sum_{i=1}^{N}
\ell\!\left(f_{\boldsymbol{\theta}}(\mathbf{x}_i), y_i\right)
+ \lambda \lVert \boldsymbol{\theta} \rVert_2^2
\tag{1}
$$

식 (1)은 다음 두 항으로 구성됩니다.

1. **데이터 적합 항:** 예측과 정답의 오차
2. **정규화 항:** 지나치게 큰 파라미터에 대한 벌점

> 수식만 제시하지 말고, 기호의 의미와 핵심 해석을 함께 적습니다.

---

## 수식 슬라이드 작성 원칙

* 한 슬라이드에는 핵심 수식 1~3개만 배치합니다.
* 새 기호는 처음 등장할 때 정의합니다.
* 유도 과정은 등호 기준으로 정렬합니다.
* 결과보다 **가정과 해석**을 먼저 설명합니다.
* 긴 수식은 여러 슬라이드로 나눕니다.

<div class="takeaway">수식은 계산을 보여주는 도구이자, 논리를 압축하는 문장입니다.</div>

---

<!-- _class: lead divider -->
# 3부 · 알고리즘과 의사코드

---

## 알고리즘 슬라이드의 기본 구조

알고리즘은 다음 순서로 설명하면 이해하기 쉽습니다.

1. **입력과 출력**
2. **핵심 아이디어**
3. **의사코드**
4. **정확성의 근거**
5. **시간·공간 복잡도**
6. **작은 실행 예시**

이 템플릿에서는 의사코드를 `text` 코드 블록으로 작성합니다.

---

<!-- _class: code-small -->
## 의사코드 예제: 이진 탐색

```text
Algorithm BinarySearch(A, target)
Input : 오름차순 배열 A[0 .. n-1], 찾을 값 target
Output: target의 인덱스, 없으면 -1

lo <- 0
hi <- n - 1

while lo <= hi do
    mid <- lo + floor((hi - lo) / 2)
    if A[mid] = target then
        return mid
    else if A[mid] < target then
        lo <- mid + 1
    else
        hi <- mid - 1

return -1
```

시간 복잡도는 $O(\log n)$, 추가 공간은 $O(1)$입니다.

---

## 이진 탐색의 불변식

반복문이 시작될 때마다 다음 명제가 성립합니다.

> target이 배열에 존재한다면, 반드시 구간 $[lo, hi]$ 안에 있다.

한 단계마다 탐색 구간의 길이는 거의 절반으로 줄어듭니다.

$$
T(n) = T\!\left(\frac{n}{2}\right) + O(1)
\quad\Rightarrow\quad
T(n)=O(\log n).
$$

정확성 설명에서는 **불변식의 초기화·유지·종료**를 차례로 제시합니다.

---

<!-- _class: code-small -->
## 의사코드 예제: 경사하강법

```text
Algorithm GradientDescent(theta_0, eta, T)
Input : 초기값 theta_0, 학습률 eta, 반복 횟수 T
Output: 갱신된 파라미터 theta

theta <- theta_0
for t <- 1 to T do
    g <- gradient L(theta)
    theta <- theta - eta * g
return theta
```

갱신식:

$$
\boldsymbol{\theta}_{t+1}
= \boldsymbol{\theta}_t
- \eta_t \nabla L(\boldsymbol{\theta}_t).
$$

---

<!-- _class: code-small -->
## 의사코드 예제: 너비 우선 탐색

```text
Algorithm BFS(G, start)
Input : 그래프 G=(V, E), 시작 정점 start
Output: 시작점에서 각 정점까지의 최단 거리

for each v in V do
    dist[v] <- infinity

dist[start] <- 0
Q <- empty queue
Q.push(start)

while Q is not empty do
    u <- Q.pop()
    for each v in Adj[u] do
        if dist[v] = infinity then
            dist[v] <- dist[u] + 1
            Q.push(v)
```

인접 리스트를 사용하면 시간 복잡도는 $O(|V|+|E|)$입니다.

---

## 점화식과 동적 계획법

피보나치 수열의 점화식:

$$
F_n =
\begin{cases}
0, & n=0, \\
1, & n=1, \\
F_{n-1}+F_{n-2}, & n\ge 2.
\end{cases}
$$

중복 계산을 저장하면 선형 시간에 계산할 수 있습니다.

```text
F[0] <- 0
F[1] <- 1
for i <- 2 to n do
    F[i] <- F[i-1] + F[i-2]
return F[n]
```

시간 $O(n)$, 공간 $O(n)$이며 두 변수만 쓰면 공간을 $O(1)$로 줄일 수 있습니다.

---

## 복잡도 표기 예제

| 유형 | 표기 | 대표 사례 |
|---|:---:|---|
| 상수 시간 | $O(1)$ | 배열 원소 접근 |
| 로그 시간 | $O(\log n)$ | 이진 탐색 |
| 선형 시간 | $O(n)$ | 한 번의 순회 |
| 선형 로그 시간 | $O(n\log n)$ | 병합 정렬 |
| 이차 시간 | $O(n^2)$ | 모든 쌍 비교 |

복잡도는 입력 크기가 커질 때의 증가율을 설명합니다. 실제 성능 비교에는 상수항, 메모리 접근, 병렬성도 함께 고려합니다.

---

<!-- _class: lead divider -->
# 4부 · C와 Python 코드

---

## 코드 블록의 기본

언어 이름을 코드 펜스 뒤에 적으면 문법 강조를 적용할 수 있습니다.

````markdown
```c
int answer = 42;
```

```python
answer = 42
```
````

발표용 코드는 다음 원칙을 권장합니다.

* 한 슬라이드에 8~18줄
* 한 줄은 가능한 한 짧게
* 핵심 분기와 반복만 남기기
* 세부 구현은 저장소 링크로 분리하기

---

<!-- _class: code-small -->
## C 예제: 이진 탐색

```c
#include <stddef.h>

int binary_search(const int *a, size_t n, int target) {
    size_t lo = 0;
    size_t hi = n;

    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;

        if (a[mid] < target)
            lo = mid + 1;
        else
            hi = mid;
    }

    return (lo < n && a[lo] == target) ? (int)lo : -1;
}
```

핵심은 반열린 구간 $[lo, hi)$를 일관되게 유지하는 것입니다.

---

<!-- _class: code-small -->
## C 예제: 동적 메모리 관리

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t n = 100;
    int *values = malloc(n * sizeof *values);

    if (values == NULL) {
        fputs("allocation failed\n", stderr);
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < n; ++i)
        values[i] = (int)(i * i);

    printf("last = %d\n", values[n - 1]);
    free(values);
    return EXIT_SUCCESS;
}
```

할당 실패를 확인하고, 소유권이 끝나는 지점에서 `free`를 호출합니다.

---

<!-- _class: code-small -->
## C 예제: 정사각 행렬 곱셈

```c
#include <stddef.h>

void matmul(const double *a, const double *b,
            double *c, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            double sum = 0.0;

            for (size_t k = 0; k < n; ++k)
                sum += a[i * n + k] * b[k * n + j];

            c[i * n + j] = sum;
        }
    }
}
```

기본 구현의 시간 복잡도는 $O(n^3)$입니다.

---

<!-- _class: code-small -->
## Python 예제: 이진 탐색

```python
from collections.abc import Sequence


def binary_search(a: Sequence[int], target: int) -> int:
    lo, hi = 0, len(a)

    while lo < hi:
        mid = lo + (hi - lo) // 2

        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid

    return lo if lo < len(a) and a[lo] == target else -1
```

타입 힌트는 입력과 반환값의 의도를 빠르게 전달합니다.

---

<!-- _class: code-small -->
## Python 예제: 경사하강법

```python
def gradient_descent(
    x0: float,
    learning_rate: float = 0.1,
    steps: int = 20,
) -> list[float]:
    """f(x) = (x - 3)^2의 최솟값을 찾는다."""
    x = x0
    history = [x]

    for _ in range(steps):
        gradient = 2.0 * (x - 3.0)
        x -= learning_rate * gradient
        history.append(x)

    return history
```

목적함수는 $f(x)=(x-3)^2$, 기울기는 $f'(x)=2(x-3)$입니다.

---

<!-- _class: code-small -->
## Python 예제: NumPy 벡터 연산

```python
import numpy as np


def standardize(x: np.ndarray) -> np.ndarray:
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)

    if np.any(std == 0):
        raise ValueError("constant feature detected")

    return (x - mean) / std


samples = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
normalized = standardize(samples)
```

배열의 축과 결과 형상을 본문에서 함께 설명하면 이해가 빨라집니다.

---

## 코드와 결과를 함께 보여주기

```python
def square(x: int) -> int:
    return x * x


values = [square(x) for x in range(5)]
print(values)
```

실행 결과:

```text
[0, 1, 4, 9, 16]
```

코드와 출력이 길다면 별도 슬라이드로 분리합니다.

---

## 코드 슬라이드 작성 원칙

* 발표에서 설명할 줄만 남깁니다.
* 함수 이름과 변수 이름으로 의도를 드러냅니다.
* 오류 처리와 경계 조건을 생략했다면 명시합니다.
* 코드 아래에는 **한 문장 요약**을 둡니다.
* 성능을 주장할 때는 입력 크기와 측정 조건을 함께 씁니다.

<div class="takeaway">코드 전체보다, 청중이 기억해야 할 한 가지 설계 선택을 강조합니다.</div>

---

<!-- _class: lead divider -->
# 5부 · 레이아웃과 마무리

---

## 목록과 체크 항목

### 순서 없는 목록

* 핵심 아이디어
  * 근거 1
  * 근거 2
* 실험 결과
* 한계와 다음 단계

### 시각적 체크 항목

* ☑ 수식과 기호, 알고리즘 복잡도 확인
* ☑ C/Python 코드 실행 확인
* ☐ 이미지와 링크 경로 확인
* ☐ PDF 최종 검토

---

<!-- _class: small -->
## 내용이 많은 슬라이드

`small, code-small, tiny, code-tiny` 클래스를 사용하면 글자를 줄일 수 있습니다.

```markdown
<!-- _class: small -->
<!-- _class: code-small -->
<!-- _class: small code-small -->
```

다만 실제 발표에서는 글자를 줄이기보다 슬라이드를 나누는 편이 좋습니다.

1. 문제 정의와 가정
2. 수식과 변수 정의
3. 알고리즘 의사코드
4. 정확성 또는 직관
5. 시간·공간 복잡도
6. 구현 세부사항
7. 실험 결과와 해석
8. 한계와 향후 연구

---

## 하이퍼링크 (Hyperlinks)

Markdown 링크 문법을 그대로 사용합니다.

* 일반 링크: [프로젝트 페이지](https://example.com)
* 설명이 있는 링크: [Marp 공식 사이트](https://marp.app "Marp")
* 저장소: [`github.com/user/project`](https://github.com/user/project)

발표 화면에는 짧은 주소만 두고, 긴 URL은 링크 텍스트 뒤에 숨기는 편이 읽기 쉽습니다.

---

## 두 컬럼 레이아웃

<div class="columns">
<div class="column">

### 제안 방법

* 계산량 감소
* 구현 단순화
* 해석 가능성 향상

</div>
<div class="column">

### 남은 과제

1. 대규모 검증
2. 잡음 강건성 평가
3. 실제 시스템 통합

</div>
</div>

> 두 컬럼에는 서로 비교 가능한 내용만 배치합니다.

---

<!-- _backgroundColor: #f0f4ff -->
<!-- _color: #1f3a8a -->

## 슬라이드별 스타일 변경

이 슬라이드는 로컬 지시어로 배경색과 글자색을 바꿉니다.

```markdown
<!-- _backgroundColor: #f0f4ff -->
<!-- _color: #1f3a8a -->
```

* `_`가 붙은 지시어는 현재 슬라이드에만 적용됩니다.
* 특별한 의미가 있을 때만 색상을 바꿉니다.

---

## 결론 및 기여

본 연구의 기여는 다음 세 가지입니다.

1. **첫 번째 기여** — 해결한 문제를 한 문장으로 설명합니다.
2. **두 번째 기여** — 제안 방법의 차별점을 설명합니다.
3. **세 번째 기여** — 검증 결과와 의미를 설명합니다.

<div class="takeaway">“제안 기법은 □□를 통해 △△ 성능을 ○○ 개선한다.”</div>

**한계와 향후 연구:** 현재 한계와 다음 검증 단계를 구체적으로 적습니다.

<p class="contact">이메일 user@example.com · 논문 arXiv:xxxx.xxxxx · 코드 github.com/user/project</p>

---

## 참고문헌 (References)

<div class="references">

1. Author, A. and Author, B., “Paper Title,” *Journal or Conference*, vol. 1, no. 2, pp. 1–10, 2026.
2. Marp Team, “Marp Documentation,” https://marp.app.
3. MathJax Consortium, “MathJax Documentation,” https://www.mathjax.org.
4. Python Software Foundation, “Python Documentation,” https://docs.python.org.
5. ISO/IEC, *Programming Languages — C*.

</div>

> 참고문헌 형식은 학회·저널의 투고 규정에 맞춰 통일합니다.

---

<!-- _class: lead -->
# 감사합니다

### 질문과 토론

<p class="contact">user@example.com · github.com/user/project</p>
