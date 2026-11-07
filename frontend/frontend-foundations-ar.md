> **ملاحظة تاريخية:** الملف ده بيوثّق مسار التعلّم القديم المبني على Vite. الـ runtime canonical حاليًا هو تطبيق Next.js App Router الموثّق في `README.md`.

# Frontend Foundations — مرجع جلسة 01

> **المشروع التعليمي:** E-commerce Frontend متصل بـ Django REST API  
> **التاريخ:** 30 أكتوبر 2026  
> **هدف الملف:** يبقى مرجع نرجع له قبل ما نبدأ React من الصفر. مش مطلوب تحفظ كل حاجة من أول قراءة.

## الفهرس

1. [الخلاصة اللي لازم تفضل في دماغك](#1-الخلاصة-اللي-لازم-تفضل-في-دماغك)
2. [الصورة الكبيرة: مين مسؤول عن إيه؟](#2-الصورة-الكبيرة-مين-مسؤول-عن-إيه)
3. [React بتعمل إيه؟](#3-react-بتعمل-إيه)
4. [Vite بتعمل إيه؟](#4-vite-بتعمل-إيه)
5. [الفرق بين Vite وVue وVanilla](#5-الفرق-بين-vite-وvue-وvanilla)
6. [React + Vite في مقابل Next.js وReact Router Framework](#6-react--vite-في-مقابل-nextjs-وreact-router-framework)
7. [CSR وSSR وSSG وHydration](#7-csr-وssr-وssg-وhydration)
8. [إزاي React بتشتغل جوه المتصفح؟](#8-إزاي-react-بتشتغل-جوه-المتصفح)
9. [إزاي نخلي التطبيق Dynamic من غير Refresh؟](#9-إزاي-نخلي-التطبيق-dynamic-من-غير-refresh)
10. [Architecture وDesign Patterns وState](#10-architecture-وdesign-patterns-وstate)
11. [Testing في الفرونت](#11-testing-في-الفرونت)
12. [قرارنا للمشروع وخريطة التعلم](#12-قرارنا-للمشروع-وخريطة-التعلم)
13. [مصادر رسمية وأسئلة مراجعة](#13-مصادر-رسمية-وأسئلة-مراجعة)

---

## 1. الخلاصة اللي لازم تفضل في دماغك

**React هي طريقة بناء الواجهة. Vite هي أداة تساعدك تطوّر وتجهّز المشروع. Next.js وReact Router Framework هما أنظمة بتاخد قرارات معمارية وبتوفر أدوات متكاملة حوالي React.**

والدرس الطبيعي اللي بعد كده **مش كتابة كود فورًا**، لكن فهم إزاي المتصفح بيشغّل React فعلًا: إيه `index.html`، وإيه `main.jsx`، وإيه الـ DOM، وإيه الفرق بين Rendering وHydration، وإزاي React بتغيّر الواجهة من غير Page Reload.

لما تفهم الرحلة دي، الـ Component Architecture والـ State Management والـ Frameworks هتبقى ليها أسباب واضحة عندك بدل ما تكون مجرد قواعد بتحفظها.

> **ملاحظة مهمة:** Vite وVue أسماء شبه بعض، لكن دورهم مختلف تمامًا. وVanilla JavaScript مش Framework أصلًا.

---

## 2. الصورة الكبيرة: مين مسؤول عن إيه؟

```text
JavaScript (اللغة)
│
├── Vanilla JavaScript
│   └── نستخدم JavaScript وBrowser APIs مباشرة بدون UI Framework
│
├── React (مكتبة UI)
│   ├── React + Vite  ← SPA نركّب فيها الأدوات اللي نحتاجها
│   ├── Next.js       ← React Framework متكامل
│   └── React Router  ← Routing فقط، أو Framework Mode
│
└── Vue (UI Framework)
    ├── Vue + Vite
    └── Nuxt (Framework مبني على Vue)

Vite = Dev Server + Build Tool
ممكن يخدم React أو Vue أو Vanilla JS وغيرهم.

Django REST Framework = Backend API مستقل ممكن يتصل بأي اختيار فوق.
```

| التقنية | نوعها | وظيفتها الأساسية | هل بديل مباشر لـ React؟ |
|---|---|---|---|
| JavaScript | لغة برمجة | المنطق والتفاعل | لا؛ React مبنية عليها |
| Vanilla JavaScript | أسلوب كتابة بدون UI Library/Framework | التعامل المباشر مع المتصفح والـ DOM | ممكن تبني بيه UI بدل React |
| React | UI Library | Components + State + Rendering | — |
| Vue | UI Framework | Components + Reactivity + Templates | **أيوه**، بديل لبناء UI |
| Vite | Dev Server / Build Tool | تشغيل التطوير وتجهيز Production Build | **لا**، بيشتغل مع React أو Vue أو Vanilla |
| Next.js | React Framework | Routing + Rendering + أدوات متكاملة | مش بديل لـ React؛ **مبني عليها** |
| React Router | Router بثلاثة Modes | التنقل، وفي Framework Mode أدوات إضافية | بيكمل React |
| Django REST Framework | Backend API Framework | بيانات، صلاحيات، Business Logic | في طبقة مختلفة |

**المقارنة الصحيحة:** React **مقابل** Vue، وReact + Vite **مقابل** Next.js كاختيارات لبناء التطبيق، لكن المقارنة الأخيرة مش تطابق كامل لأن Vite أداة وNext.js Framework.

---

## 3. React بتعمل إيه؟

React بتساعدنا نكتب الواجهة كـ **Components** صغيرة، وكل Component بتوصف الجزء المطلوب ظهوره بناءً على **Props** و**State**.

```jsx
function ProductCard({ product }) {
  return (
    <article>
      <h2>{product.name}</h2>
      <p>{product.price} EGP</p>
      <button>Add to Cart</button>
    </article>
  );
}
```

- **Component:** جزء واجهة قابل للتقسيم وإعادة الاستخدام.
- **Props:** بيانات جاية للـ Component من الأب؛ عادةً نتعامل معاها كمدخلات للقراءة.
- **State:** بيانات بتتغير وReact تقدر تستخدم التغيير ده لتحديث الواجهة.
- **JSX:** Syntax يشبه HTML، لكنه بيتحوّل إلى JavaScript أثناء تجهيز الكود؛ مش HTML خام.

React وحدها **مش** بتفرض طريقة واحدة للـ Routing أو API Fetching أو تنظيم كل المشروع أو الـ Deployment. نختار أدوات لهذه المهام حسب الحاجة.

---

## 4. Vite بتعمل إيه؟

Vite بتعمل وظيفتين رئيسيتين:

### وقت التطوير (Development)

- بتشغّل **Dev Server** يخدم ملفات المشروع للمتصفح.
- بتتعامل مع الـ Modules، وبتعمل تحويلات لازمة لملفات زي JSX باستخدام إعدادات/Plugins مناسبة.
- بتوفر **HMR (Hot Module Replacement)**: لما نعدّل ملف، التغيير ممكن يظهر بسرعة من غير Full Page Reload (وأحيانًا يحصل Reload حسب التعديل).

### وقت النشر (Production)

- الأمر `npm run build` بيجهّز نسخة Production محسّنة من الملفات.
- مع قالب Vite المعتاد الناتج بيظهر في `dist/` (ما لم نغيّر الإعداد).
- مخرجات الـ SPA غالبًا HTML وCSS وJavaScript وAssets ثابتة، وممكن نخدمها من Static Hosting.

```text
أثناء التطوير:
.jsx / .css  -> Vite Dev Server -> Browser

وقت الـ Production:
.jsx / .css  -> Vite Build      -> dist/ (assets optimized)
```

**Vite لا تُدير State الخاصة بالواجهة، ولا هي المسؤولة عن التنقل بين صفحات React أثناء التشغيل.** دي مسؤوليات React والـ Router وأدوات إدارة البيانات.

### أمثلة إنشاء مشروع (للمرجع فقط — لسه مش وقت التنفيذ)

```bash
# React + Vite
npm create vite@latest ecommerce-frontend -- --template react

# Vue + Vite
npm create vite@latest vue-playground -- --template vue

# Vanilla JavaScript + Vite
npm create vite@latest vanilla-playground -- --template vanilla
```

وبعد الدخول لأي مشروع منهم، غالبًا:

```bash
npm install
npm run dev
npm run build
```

> ملحوظة: لازم إصدار Node.js مناسب لنسخة Vite الحالية. راجع [دليل Vite](https://vite.dev/guide/) وقت التنفيذ بدل الاعتماد على رقم إصدار ثابت.

---

## 5. الفرق بين Vite وVue وVanilla

### أول حاجة: الاسم مش معناه إنهم نفس النوع

- **Vite:** أداة تشغّل وتبني المشروع. مش بتكتبلك UI Components.
- **Vue:** Framework لبناء واجهة ديناميكية. عنده Components وReactivity وTemplate Syntax.
- **Vanilla JavaScript:** JavaScript عادية بدون React أو Vue؛ إنت بتتعامل مع الـ DOM والـ Events بنفسك.

**ممكن تشتغل بـ `Vue + Vite`، أو `React + Vite`، أو `Vanilla + Vite`.** بالتالي سؤال «أختار Vite ولا Vue؟» مش دقيق؛ ممكن تختار الاتنين مع بعض.

### نفس المثال بثلاث طرق: زرار Counter

**Vanilla JavaScript** — إنت بتلاقي العنصر وبتحدّث نصّه بنفسك:

```html
<button id="counter">Count: 0</button>
<script>
  let count = 0;
  const button = document.querySelector('#counter');
  button.addEventListener('click', () => {
    count += 1;
    button.textContent = `Count: ${count}`;
  });
</script>
```

**React** — بتغيّر الـ State وReact بتحدّث الواجهة:

```jsx
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount((previous) => previous + 1)}>
      Count: {count}
    </button>
  );
}
```

**Vue** — بتستخدم Reactive Value وTemplate؛ المثال ده محتوى ملف `.vue`:

```vue
<script setup>
import { ref } from 'vue';
const count = ref(0);
</script>

<template>
  <button @click="count++">Count: {{ count }}</button>
</template>
```

| السؤال | Vanilla JS | React | Vue |
|---|---|---|---|
| مين بيدير تحديث الـ UI؟ | إنت غالبًا بتحدّث الـ DOM بنفسك | React | Vue |
| Components جاهزة كنمط أساسي؟ | تبني تنظيمك بنفسك/تستخدم Web Components | نعم | نعم |
| طريقة وصف الواجهة | HTML + JS/DOM APIs | JSX | Templates (وغالبًا ملفات `.vue`) |
| مناسب لإيه؟ | تعلم أساس الويب وأجزاء بسيطة | تطبيقات Components كبيرة ومتغيرة | تطبيقات UI كبيرة ومتغيرة |
| هل يحتاج Vite بالضرورة؟ | لا | لا | لا |

**إمتى Vanilla كويسة؟** لو عايز تفهم DOM وEvents أو تعمل صفحة صغيرة ومحدودة؛ وممكن تستخدمها في تطبيق كبير لكن إدارة التعقيد هتبقى عليك.

**إمتى React أو Vue؟** لما الواجهة تكبر وفيها Components متعددة وحالات كتير وتتغير باستمرار. الاتنين اختياران حقيقيان لبناء UI، لكن أسلوب كتابة الكود والتعامل مع التحديثات مختلف.

**إحنا هنستخدم React** لأن هدف المشروع التدرب عليها، مش لأن Vue «غلط» أو أقل جودة.

---

## 6. React + Vite في مقابل Next.js وReact Router Framework

### React + Vite

غالبًا بنستخدمهم لبناء **SPA**، ونضيف بنفسنا:

- React Router للتنقل؛
- API layer للتواصل مع Django؛
- حلول Server State مثل TanStack Query عند الحاجة؛
- تنظيم المشروع والـ Tests.

ميزة التعلم هنا إنك بتشوف كل طبقة وهي بتتضاف و**ليه**.

### Next.js

Next.js Framework مبني على React، بيوفر مثلًا:

- File-system routing (`app/products/page.jsx` تمثل `/products` في App Router)؛
- Server Rendering وStatic Rendering وClient Components؛
- Layouts، وأدوات للـ Data Fetching والـ Server-side Logic.

وجود Next.js **مش معناه لازم تستغنى عن Django**؛ تقدر تخلي Django هو الـ Backend API وتستخدم Next.js في طبقة الويب.

### React Router

React Router عنده 3 أنماط استعمال أساسية:

1. **Declarative Mode:** Routing بسيط بـ `<BrowserRouter>` و`<Routes>`.
2. **Data Mode:** يزيد loaders وactions وإدارة حالات التنقل/التحميل.
3. **Framework Mode:** يضيف أدوات بناء وتنظيم ويدعم استراتيجيات SPA/SSR/Static Rendering.

مش كل مشروع فيه React Router بقى Full-stack Framework؛ ده بيتوقف على الـ Mode وطريقة إعداد المشروع.

### في سطر واحد

| الاختيار | مين بيقرر تفاصيل الـ Architecture؟ |
|---|---|
| React + Vite | إنت بتختار معظم طبقات التطبيق |
| Next.js | الـ Framework بيوفر قرارات وأدوات جاهزة أكتر |
| React Router Framework | بيوفر Routing/Data/Rendering conventions مع مرونة في الاختيار |

### أسماء أخرى تعرف إنها موجودة

- **TanStack Start:** Full-stack React Framework مبني على TanStack Router.
- **Astro:** Web Framework للمواقع المعتمدة على المحتوى ويدعم استخدام React Components، لكنه مش React-only Framework.
- **Expo:** Framework لبناء تطبيقات React Native للهواتف (ويدعم الويب).
- **Remix v2:** لو لقيته في كورسات قديمة، راجع علاقة انتقال تطبيقات Remix v2 إلى React Router v7 Framework Mode.

---

## 7. CSR وSSR وSSG وHydration

دي **استراتيجيات تجهيز وعرض الصفحة**؛ مش أسماء مكتبات، ومش معناها وحدها إن التطبيق Dynamic أو Static من ناحية البيانات.

| المصطلح | إيه اللي بيحصل؟ | مثال شائع |
|---|---|---|
| **CSR** (Client-Side Rendering) | المتصفح يشغّل JavaScript، وReact تعرض محتوى الصفحة | React + Vite SPA |
| **SSR** (Server-Side Rendering) | السيرفر يولّد HTML للطلب، والمتصفح يستقبله ويعرضه | Next.js لبعض الصفحات |
| **SSG** (Static Site Generation) | HTML يتجهّز وقت الـ Build بدل توليده لكل طلب | صفحات المحتوى الثابت |
| **Hydration** | React تربط المنطق التفاعلي بـ HTML متولّد مسبقًا من السيرفر | تطبيقات SSR/SSG التفاعلية |

**معلومتان مهمتان:**

- CSR تقدر تكون Dynamic تمامًا؛ الـ Dynamic مش محتاج SSR.
- **Hydration مش نفس Rendering.** في تطبيق CSR بسيط نستخدم عادةً `createRoot`؛ لما HTML يكون متولّد مسبقًا من React على السيرفر، نستخدم عادةً `hydrateRoot` عشان نربط التفاعل بالمحتوى الموجود.

وفي Next.js يوجد مفهوم **React Server Components (RSC)**؛ ده مرتبط بمكان تنفيذ الـ Components وحدود السيرفر/العميل، ومش مجرد اسم تاني لـ SSR. هنأجله لوقت مناسب.

---

## 8. إزاي React بتشتغل جوه المتصفح؟

**دي خريطة الدرس الجاي، مش مطلوب نغوص في التفاصيل النهاردة.**

```text
المستخدم يفتح / في Browser
         │
         ▼
المتصفح يطلب index.html
         │
         ▼
index.html فيه عنصر <div id="root"></div>
وفيه script يبدأ من /src/main.jsx
         │
         ▼
main.jsx يهيّئ React Root
         │
         ▼
<App /> (Component Tree)
         │
         ▼
React تحسب المطلوب عرضه وتحدّث Browser DOM
```

**`index.html`** في قالب Vite نقطة الدخول للصفحة، وبيشير إلى `main.jsx`:

```html
<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /></head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**`main.jsx`** عادةً يربط React بالعنصر الموجود في HTML:

```jsx
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(<App />);
```

**`App.jsx`** هي Component أساسية في الشجرة (والاسم اختيار شائع، مش قانون في React):

```jsx
export default function App() {
  return <h1>My Store</h1>;
}
```

**DOM (Document Object Model):** تمثيل شجري لعناصر الصفحة داخل المتصفح (`document` والعناصر اللي تحته). في Vanilla JS ممكن تعدّلها باستخدام `document.querySelector(...)`، وفي React غالبًا بنوصف الواجهة عبر Components ونسيب React تدير التحديثات.

**Render vs Commit:** لما State تتغير، React تشغّل منطق Rendering لحساب الشكل المطلوب، وبعدها مرحلة Commit تطبق التغييرات المطلوبة على الـ DOM. إعادة الـ Render مش معناها بالضرورة تغيير كل عناصر الصفحة.

---

## 9. إزاي نخلي التطبيق Dynamic من غير Refresh؟

مهم نفرق بين **أربع حاجات مختلفة**:

1. **Full Page Reload:** المتصفح يعيد تحميل الصفحة نفسها (زي F5).
2. **React Re-render:** React تعيد حساب واجهة Component بعد تغيّر State أو Props؛ مش Reload للصفحة.
3. **Data Refetch:** Request جديد للـ API للحصول على بيانات أحدث؛ ممكن يحصل من غير Reload.
4. **HMR:** تحديث كود أثناء *التطوير* لما تعدّل ملفات المشروع؛ ميزة من Vite مش آلية التنقل عند المستخدم.

في متجرنا الـ Flow الطبيعي:

```text
المستخدم يزور /products
        │
        ▼
React Router يحدد صفحة المنتجات
        │
        ▼
Data Hook أو Page Logic يطلب بيانات من Django API
        │
        ├── Loading
        ├── Error
        ├── Empty
        └── Success → ProductCard components

المستخدم يضغط منتج → Client-side Navigation
بدون Full Page Reload
```

والأهم: **تغيير الـ URL والتنقل بدون Reload شيء، والحفاظ على بيانات حديثة شيء مختلف**. هنستخدم Routing + State + Data Fetching، وكل جزء له مسؤولية.

---

## 10. Architecture وDesign Patterns وState

بما إن الهدف تعليمي، مش هننشئ عشرات الفولدرات من أول يوم. هنبدأ صغير، ولما يكبر المشروع نميل إلى **Feature-Based Architecture**:

```text
src/
├── app/
│   ├── App.jsx
│   └── router.jsx
├── features/
│   ├── products/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── tests/
│   ├── auth/
│   ├── cart/
│   └── orders/
├── shared/
│   ├── components/
│   └── lib/
└── main.jsx
```

> **ده تصور مستقبلي مش Checklist نعملها كلها دلوقتي.** مكان الملف يتحدد بناءً على مسؤوليته، مش عشان نملأ مجلدات.

### Design Patterns هنقابلها أثناء البناء

- **Component Composition:** نجمع Components صغيرة بدل Component ضخم.
- **Separation of Concerns:** نفصل جلب البيانات عن طريقة عرضها.
- **Custom Hooks:** نعيد استخدام منطق React المرتبط بالـ Hooks عند الحاجة.
- **API Service Layer:** نخلي تفاصيل طلبات HTTP في مكان واضح بدل تكرارها في UI.
- **Context / Provider:** لمشاركة بعض البيانات أو Dependencies من غير تمرير Props عبر مستويات كثيرة عند الحاجة.
- **Feature-Based Organization:** نجمع ملفات كل Feature مع بعضها.

### أنواع الـ State

| النوع | مثال | اختيار أولي |
|---|---|---|
| Local UI State | فتح Modal، Toggle | `useState` |
| URL State | البحث/الفلترة/رقم الصفحة | Search Params في URL |
| Server State | قائمة المنتجات وبيانات السلة | نفهم `fetch` الأول ثم TanStack Query |
| Shared Client State | قيمة يحتاجها أكثر من جزء | Context عند الحاجة |

**مثال:** رابط `/products?name=Samsung&page=2` مفيد لأن الفلاتر تبقى قابلة للمشاركة، وبتفضل موجودة بعد Refresh.

### التصور المعماري الخاص بمشروعنا

```text
Browser (React + Vite)
        │ HTTP / JSON
        ▼
Django REST Framework
        │
        ▼
Database
```

Django مسؤولة عن بيانات المنتجات والمستخدمين والطلبات والـ Business Rules. React مسؤولة عن تجربة المستخدم وعرض الحالات والتفاعلات، **ومش بنثق في أسعار أو صلاحيات قادمة من المتصفح بدل السيرفر**.

---

## 11. Testing في الفرونت

زي ما بنختبر الباك إند، هنختبر الفرونت على مراحل:

| المستوى | أداة شائعة | بنختبر إيه؟ |
|---|---|---|
| Unit | Vitest | Function لحساب سعر أو Validation |
| Component / Integration | React Testing Library + MSW | عرض Loading / Products / Error مع Mock API |
| End-to-End | Playwright | رحلة مستخدم حقيقية في المتصفح |

مش كل Test لازم Django تكون شغالة فيها. في اختبارات نقدر نعمل Mock للـ API، وبعدها اختبارات Integration فعلية حسب الحاجة.

---

## 12. قرارنا للمشروع وخريطة التعلم

### اختيارنا المبدئي

**React + Vite + React Router**، مع **Django REST Framework** الموجود عندنا.

مش عشان Next.js أو Vue اختيارات سيئة؛ لكن عشان هدفنا نتعلم نفهم قرارات الـ Frontend Architecture ونضيف الأدوات بإيدنا واحدة واحدة.

### هنمشي بالترتيب ده

- [ ] **الدرس 02 — المتصفح:** `index.html` → `main.jsx` → `App.jsx` → DOM → Rendering.
- [ ] **الدرس 03 — بداية المشروع:** نعمل مشروع Vite صغير ونفهم كل ملف اتولد وليه.
- [ ] **الدرس 04 — React Basics:** Components, Props, State, Events, Lists.
- [ ] **الدرس 05 — أول Feature حقيقية:** Products Page متصلة بـ Django، بحالات Loading/Error/Empty/Success.
- [ ] **الدرس 06 — Separation of Concerns:** نفصل الـ API Layer والـ UI ونقرر إمتى نحتاج Custom Hook.
- [ ] **الدرس 07 — Navigation:** React Router، Dynamic Routes، URL State.
- [ ] **الدرس 08 — Server State:** Refetch, Caching, TanStack Query.
- [ ] **الدرس 09 — Auth & Cart:** JWT، التعامل مع API Errors، السلة.
- [ ] **الدرس 10 — Testing & Refactoring:** Vitest وReact Testing Library وPlaywright.

**طريقة الشغل:** نفهم المشكلة → نرسم Data Flow صغير → إنت تختار تقسيمتك الأولية → تكتب الكود → نعمل Code Review → نختبر ونحسّن.

### أول Feature هنفكر فيها بعد الأساسيات

| بند | تعريف |
|---|---|
| Feature | Products Listing |
| Route | `/products` |
| API | `GET /api/products/` (نتحقق من Contract الفعلي عند التشغيل) |
| UI States | Loading / Error / Empty / Success |
| أسئلة Architecture | مين يطلب البيانات؟ ومين يعرضها؟ وفين نخزنها؟ |
| اختبار | هل المنتجات ظهرت؟ إيه اللي يحصل لو الـ API فشل؟ |

**مطلوب منك دلوقتي:** ولا حاجة تتنفّذ. احتفظ بالمرجع؛ في الجلسة الجاية هنفتح `index.html` و`main.jsx` ونتتبع الكود من أول المتصفح، وبعدين نبدأ إنشاء المشروع خطوة خطوة.

---

## 13. مصادر رسمية وأسئلة مراجعة

### المصادر

- [React — Learn](https://react.dev/learn)
- [React — Creating a React App](https://react.dev/learn/creating-a-react-app)
- [React — Render and Commit](https://react.dev/learn/render-and-commit)
- [React — createRoot](https://react.dev/reference/react-dom/client/createRoot)
- [React — hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)
- [Vite — Getting Started](https://vite.dev/guide/)
- [Vue — Introduction](https://vuejs.org/guide/introduction)
- [React Router — Picking a Mode](https://reactrouter.com/start/modes)
- [Next.js — App Router](https://nextjs.org/docs/app)
- [MDN — DOM](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Anatomy_of_the_DOM)
- [Vitest](https://vitest.dev/guide/)، [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)، [Playwright](https://playwright.dev/docs/intro)

### أسئلة تراجع بيها نفسك

1. هل Vite بديل لـ React؟ وليه؟
2. هل أقدر أعمل Vue + Vite؟ وهل أقدر أعمل Vanilla + Vite؟
3. لو الـ State اتغيرت، ده يعني Browser Reload ولا React Re-render؟
4. إيه الفرق بين Data Refetch وHMR؟
5. مين مسؤول عن بيانات وأسعار الطلبات: Django ولا المتصفح؟
6. إمتى ممكن أحتاج SSR بدل CSR؟
7. إيه وظيفة `index.html`، وإيه وظيفة `main.jsx`؟

---

**الجملة المفتاحية:** *افهم مين مسؤول عن إيه قبل ما تختار أداة أو تعمل فولدر جديد.*
