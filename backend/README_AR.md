# شرح المشروع بالعربي

المشروع ده Backend لمتجر single-vendor معمول بـ Django وDjango REST Framework، والهدف الأساسي منه إنك تدرس architecture نظيفة وقابلة للتوسعة، مش مجرد endpoints شغالة.

## ليه Modular Monolith؟

المتجر فيه domains مترابطة جدًا: المنتج والـ SKU والمخزون والسلة والطلب والكوبون والنقاط والدفع. فصلهم microservices هنا هيزود complexity من غير فايدة تعليمية. في نفس الوقت، حشر كل حاجة في app واحدة هيخلي الكود صعب. علشان كده التقسيم الحالي ثلاث apps:

- `account`: المستخدم، profile، addresses، authentication، notifications، audit.
- `product`: catalog، variants، inventory، reviews، wishlist.
- `order`: cart، shipping، checkout، orders، coupons، loyalty، COD، returns/refunds، reports.

كل app فيها implementation واحدة بس. مفيش `v2` files أو API قديمة مستخبية.

## كل نوع كود مكانه فين؟

- `models.py`: شكل البيانات والـ database constraints والعلاقات. الـ model مش مكان workflow طويل.
- `serializers.py`: شكل request/response والـ input validation المحلي. ميتوثقش فيه stock أو money consistency لوحده.
- `views.py`: HTTP، permissions، اختيار serializer، واستدعاء service/selector.
- `services.py`: العمليات اللي بتغير أكتر من row أو محتاجة transaction/locking/idempotency.
- `selectors.py`: queries مركبة للقراءة والتقارير من غير side effects.
- `urls.py`: المسارات الفعلية للـ API.
- `tests/`: model/API/service/integration/concurrency behavior.

## الـ database والعلاقات

`Product` هو الوصف العام، لكن البيع الفعلي بيتم من `ProductVariant`: كل variant عنده SKU وسعر ومخزون. السلة والطلب بيرجعوا للvariant، والـ order item بياخد snapshot للاسم وSKU والسعر والoptions وقت الشراء.

`Order` بيحفظ address وshipping وdiscount totals كـ snapshots علشان التاريخ ميتغيرش لو المستخدم عدل عنوانه أو الإدارة عدلت السعر. كل تغيير status بيتسجل في timeline.

النقاط مش integer على user وخلاص. `LoyaltyWallet` فيه الرصيد الحالي، وكل حركة موجودة في `LoyaltyTransaction` بـ unique event key. لو نقاط مكتسبة اتصرفت وبعدين حصل return، الرصيد ميبقاش سالب؛ الفرق بيتسجل `outstanding_clawback` ويتخصم من earnings الجاية.

## checkout بيحصل إزاي؟

1. الـ view يتحقق من request shape والـ ownership.
2. `checkout()` يفتح `transaction.atomic()` ويقفل user/cart/variants/coupon/wallet.
3. السيرفر يعيد حساب السعر من الـ database، مش من body.
4. يتأكد من stock وshipping zone والكوبون والنقاط.
5. ينشئ order وimmutable items وCOD payment وtimeline.
6. يخصم stock ويسجل inventory movements والloyalty/coupon events.
7. يمسح السلة ويثبت idempotency result.
8. notification تتعمل بعد نجاح commit فقط.

نفس `Idempotency-Key` مع نفس body بيرجع نفس الطلب؛ نفس المفتاح مع body مختلف بيرفض.

## Authentication وpermissions

فيه custom `User` مبني على Django `AbstractUser`. الـ username هو login identifier، والemail normalized وunique في الـ database. JWT access قصير، والrefresh بيتعمله rotation/blacklist. كل private queryset بيتفلتر بالowner، والstaff endpoints بتستخدم `IsAdminUser`.

## إزاي تزود feature؟

ابدأ بالbusiness rule والconstraint، بعدين model/migration لو محتاج، service للwrite workflow، selector للread query، serializer للcontract، view رفيعة، URL، tests، وبعدها OpenAPI/docs. متحطش logic مالي في signal أو view.

لشرح تفصيلي امشِ بالترتيب ده:

1. [CODEBASE_WALKTHROUGH.md](docs/CODEBASE_WALKTHROUGH.md)
2. [ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. [DATABASE.md](docs/DATABASE.md)
4. [BUSINESS_RULES.md](docs/BUSINESS_RULES.md)
5. [API_REFERENCE.md](docs/API_REFERENCE.md)
6. [TESTING.md](docs/TESTING.md)

أوامر التشغيل موجودة في [README.md](README.md)، وSwagger على `/api/docs/`.
