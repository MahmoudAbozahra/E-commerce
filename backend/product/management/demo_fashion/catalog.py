# ruff: noqa: E501
"""Backend-owned demo fashion catalogue and its exact media sources."""

DEMO_BRAND_SLUG = "atelier-cairo"
DEMO_ROOT_CATEGORY_SLUG = "apparel"


def product(slug, name, color, price, sources, *, featured=False, availability="available"):
    return {
        "slug": slug,
        "name": name,
        "color": color,
        "price": price,
        "sources": tuple(sources),
        "featured": featured,
        "availability": availability,
    }


CATEGORY_GROUPS = (
    {
        "slug": "hoodies-sweatshirts", "name": "Hoodies & Sweatshirts", "description": "Relaxed layers, zip hoodies and heavyweight studio sweats.", "sizes": ("S", "M", "L", "XL"),
        "products": (
            product("clay-zip-hoodie", "Clay Zip Hoodie", "clay", "1890.00", ("File:Hoodie-szmurlo.jpg",), featured=True),
            product("ink-studio-hoodie", "Ink Studio Hoodie", "ink", "1790.00", ("File:Kid-2928268.jpg",), featured=True),
            product("oat-loopback-sweatshirt", "Oat Loopback Sweatshirt", "oat", "1690.00", ("File:2008 Butterfly Hoodie by Damien Hirst for Adrian Nyman 02.jpg", "File:2008 Butterfly Hoodie by Damien Hirst for Adrian Nyman 01.jpg")),
            product("cobalt-pullover-hoodie", "Graphic Pullover Hoodie", "black", "1820.00", ("File:“Girls Just Want To Have Fun” hoodie collection.jpg",), featured=True),
            product("rose-cropped-sweatshirt", "Studio Deployable Hoodie", "black", "1580.00", ("File:Deployable Hoodie, Diana Eng's Fairytale Fashion Show at Eyebeam NYC 20100224.7D.03498.P1.L1.SQ SML (4388311682).jpg",), availability="limited"),
            product("charcoal-track-hoodie", "Charcoal Track Hoodie", "charcoal", "1760.00", ("File:Black Zipper Hoodie Graphic T Shirt.jpg",), availability="out"),
        ),
    },
    {
        "slug": "shirts", "name": "Shirts", "description": "Striped, Oxford and relaxed shirts with an editorial archive influence.", "sizes": ("S", "M", "L", "XL"),
        "products": (
            product("sky-stripe-shirt", "Sky Archive Shirt", "sky", "1350.00", ("File:Shirt MET 2006.132 F.jpg",), featured=True),
            product("white-oxford-shirt", "White Oxford Shirt", "white", "1490.00", ("File:Shirt MET 08.180.969.jpg",)),
            product("sage-camp-collar-shirt", "Sage Camp Collar Shirt", "sage", "1420.00", ("File:Shirt MET 08.180.970.jpg",)),
            product("cocoa-linen-shirt", "Cocoa Linen Shirt", "cocoa", "1570.00", ("File:Shirt MET 1980.447 B.jpg",)),
            product("navy-relaxed-shirt", "Navy Relaxed Shirt", "navy", "1460.00", ("File:Shirt MET 09.68.603ab.jpg",), availability="limited"),
            product("blush-poplin-shirt", "Blush Poplin Shirt", "blush", "1520.00", ("File:Shirt MET 2004.170 F.jpg", "File:Shirt MET 2004.170 B.jpg")),
        ),
    },
    {
        "slug": "denim", "name": "Denim", "description": "Straight, relaxed and wide-leg denim cuts for everyday rotation.", "sizes": ("30", "32", "34", "36"),
        "products": (
            product("indigo-straight-jeans", "Indigo Straight Jeans", "indigo", "1980.00", ("File:Jeans MET 1978.175.2 F.jpg", "File:Jeans MET 1978.175.2 B.jpg"), featured=True),
            product("washed-wide-leg-jeans", "Washed Wide-Leg Jeans", "washed blue", "2050.00", ("File:Jeans MET 1978.175.1 F.jpg", "File:Jeans MET 1978.175.1 B.jpg")),
            product("black-tapered-denim", "Black Tapered Denim", "black", "1920.00", ("File:Jeans MET 1978.175.3 F.jpg", "File:Jeans MET 1978.175.3 B.jpg")),
            product("stone-relaxed-jeans", "Stone Relaxed Jeans", "stone", "1880.00", ("File:Woman wearing jeans - 1.jpg",)),
            product("raw-studio-jeans", "Raw Studio Jeans", "raw indigo", "2150.00", ("File:Jeans Gul&Blå i modellen Dallas.jpg",), availability="limited"),
            product("midnight-sculpt-jeans", "Midnight Sculpt Jeans", "midnight", "2070.00", ("File:Plus size model with black Peach Queen Butt lift jeans - Aug 2024.jpg",)),
        ),
    },
    {
        "slug": "trousers-cargos", "name": "Trousers & Cargos", "description": "Utility cargos and tailored trousers in practical, easy silhouettes.", "sizes": ("30", "32", "34", "36"),
        "products": (
            product("sand-utility-cargo", "Sand Utility Cargo", "sand", "1720.00", ("File:Trousers MET 1997.109 F.jpg", "File:Trousers MET 1997.109 B.jpg"), featured=True),
            product("olive-relaxed-cargo", "Olive Relaxed Cargo", "olive", "1780.00", ("File:Trousers MET CI39.87 F.jpg",)),
            product("charcoal-tailored-trouser", "Charcoal Tailored Trouser", "charcoal", "1860.00", ("File:Trousers MET 1978.88.12 B.jpg",)),
            product("taupe-pleated-pant", "Taupe Pleated Pant", "taupe", "1810.00", ("File:Trousers MET 26.231.17 F.jpg", "File:Trousers MET 26.231.17 B.jpg")),
            product("ink-wide-leg-trouser", "Ink Wide-Leg Trouser", "ink", "1930.00", ("File:Trousers MET CI40.173.9 F.jpg",), availability="limited"),
            product("clay-drawstring-pant", "Clay Drawstring Pant", "clay", "1640.00", ("File:Trousers MET 1983.7.2 F.jpg", "File:Trousers MET 1983.7.2 B.jpg")),
        ),
    },
    {
        "slug": "jackets-overshirts", "name": "Jackets & Overshirts", "description": "Light outer layers, workwear forms and structured evening jackets.", "sizes": ("S", "M", "L", "XL"),
        "products": (
            product("sage-utility-overshirt", "Sage Utility Overshirt", "sage", "1650.00", ("File:Jacket (AM 740158-3).jpg",), featured=True),
            product("indigo-denim-jacket", "Indigo Denim Jacket", "indigo", "2390.00", ("File:Denim jacket and leather pants.jpg",)),
            product("black-harrington-jacket", "Black Harrington Jacket", "black", "2480.00", ("File:Harrington-jacket-marque-francaise-Harrington-bleu-Tartan-Royal-Stewart-byRundvald.jpg",)),
            product("oat-smoking-jacket", "Oat Smoking Jacket", "oat", "2690.00", ("File:Smoking jacket MET C.I.40.60.2 F.jpg", "File:Smoking jacket MET C.I.40.60.2 B.jpg")),
            product("rust-sequin-jacket", "Rust Sequin Jacket", "rust", "2820.00", ("File:Vintage Sequin Duster Jacket.jpg",), availability="limited"),
            product("midnight-windbreaker", "Midnight Windbreaker", "midnight", "2260.00", ("File:Windbreaker Jacket, Hood Outside.jpg",)),
        ),
    },
    {
        "slug": "knitwear", "name": "Knitwear", "description": "Textured pullovers, cardigans and soft archive-inspired knits.", "sizes": ("S", "M", "L", "XL"),
        "products": (
            product("sand-knit-pullover", "Sand Knit Pullover", "sand", "1490.00", ("File:Sweater MET 129567.jpg",), featured=True),
            product("moss-texture-knit", "Moss Texture Knit", "moss", "1590.00", ("File:Jersei-coll-alt.jpg",)),
            product("ivory-rib-cardigan", "Ivory Rib Cardigan", "ivory", "1730.00", ("File:Sweater (clothing).jpg",)),
            product("cobalt-crew-knit", "Cobalt Crew Knit", "cobalt", "1680.00", ("File:Sweater MET 14.134.18 F.jpg", "File:Sweater MET 14.134.18 B.jpg")),
            product("rose-brushed-pullover", "Rose Brushed Pullover", "rose", "1760.00", ("File:Sweater MET C.I.45.79.51 F.jpg", "File:Sweater MET C.I.45.79.51 B.jpg"), availability="limited"),
            product("charcoal-knit-set", "Charcoal Knit Set", "charcoal", "2210.00", ("File:1970s Missoni sweater and skirt set, purple, red and green plaid knit.jpg",)),
        ),
    },
    {
        "slug": "dresses", "name": "Dresses", "description": "Day-to-evening dresses with column, wrap and softly structured shapes.", "sizes": ("XS", "S", "M", "L"),
        "products": (
            product("black-column-dress", "Black Column Dress", "black", "2380.00", ("File:Dress MET 1989.323front.jpg", "File:Dress MET 1989.323back.jpg"), featured=True),
            product("ivory-wrap-dress", "Ivory Wrap Dress", "ivory", "2240.00", ("File:Dress MET 1990.24 B.jpg",)),
            product("clay-midi-dress", "Clay Midi Dress", "clay", "2310.00", ("File:Dress MET DT202838.jpg",)),
            product("sage-shirt-dress", "Sage Shirt Dress", "sage", "2180.00", ("File:Dress MET 1978.477.11 F.jpg", "File:Dress MET 1978.477.11 B.jpg")),
            product("cobalt-evening-dress", "Cobalt Evening Dress", "cobalt", "2890.00", ("File:Dress MET DT7538.jpg", "File:Dress MET DT7539.jpg"), availability="limited"),
            product("rose-tiered-dress", "Archive Tiered Dress", "black and ivory", "2420.00", ("File:Evening dress MET 87V F485R2.jpg",)),
        ),
    },
    {
        "slug": "skirts-blouses", "name": "Skirts & Blouses", "description": "Pleated and wrap skirts paired with polished, softly draped blouses.", "sizes": ("XS", "S", "M", "L"),
        "products": (
            product("ink-pleated-skirt", "Ink Pleated Skirt", "ink", "1560.00", ("File:Skirt MET 20.81.4.jpg",), featured=True),
            product("oat-wrap-skirt", "Oat Wrap Skirt", "oat", "1490.00", ("File:Skirt MET 26.265.48.jpg",)),
            product("clay-midi-skirt", "Clay Midi Skirt", "clay", "1620.00", ("File:Skirt MET 1973.110.2ab F.jpg", "File:Skirt MET 1973.110.2ab S.jpg")),
            product("ivory-silk-blouse", "Ivory Silk Blouse", "ivory", "1710.00", ("File:Blouse MET CI63.38.3 F.jpg", "File:Blouse MET CI63.38.3 B.jpg")),
            product("sage-collar-blouse", "Sage Collar Blouse", "sage", "1650.00", ("File:Blouse MET 1980.408.4 F.jpg", "File:Blouse MET 1980.408.4 B.jpg"), availability="limited"),
            product("cobalt-draped-blouse", "Cobalt Draped Blouse", "cobalt", "1680.00", ("File:Blouse MET 1983.93.2 F.jpg",)),
        ),
    },
    {
        "slug": "coats-outerwear", "name": "Coats & Outerwear", "description": "Longline coats and evening outerwear for cooler city days.", "sizes": ("S", "M", "L", "XL"),
        "products": (
            product("camel-studio-coat", "Camel Studio Coat", "camel", "3290.00", ("File:Coat MET 1981.210.4 F.jpeg",), featured=True),
            product("charcoal-wool-coat", "Charcoal Wool Coat", "charcoal", "3480.00", ("File:Coat MET CI40.196 F.jpg",)),
            product("ivory-evening-coat", "Ivory Evening Coat", "ivory", "3620.00", ("File:Coat MET 1993.359 F.jpg", "File:Coat MET 1993.359 B.jpg")),
            product("rust-belted-coat", "Rust Belted Coat", "rust", "3370.00", ("File:Evening coat MET 1991.187.7 F.jpg",), availability="limited"),
            product("sage-lightweight-coat", "Sage Lightweight Coat", "sage", "3180.00", ("File:Evening coat MET 1978.46 B.jpg",)),
            product("midnight-archive-coat", "Midnight Archive Coat", "midnight", "3540.00", ("File:Coat MET 1976.333 B.jpg",)),
        ),
    },
    {
        "slug": "coordinated-sets", "name": "Coordinated Sets", "description": "Complete smart-casual looks photographed as coherent, multi-angle outfits.", "sizes": ("XS", "S", "M", "L"),
        "products": (
            product("monochrome-city-set", "Monochrome City Set", "black and white", "2760.00", ("File:Casual Fashion 2022.jpg", "File:Casual Fashion 2022 - 51908733728.jpg", "File:Casual Fashion 2022 - 51908640986.jpg"), featured=True),
            product("black-column-set", "Black Column Set", "black", "2640.00", ("File:Casual Fashion 2022 - 51908729333.jpg", "File:Casual Fashion 2022 - 51908958824.jpg")),
            product("gingham-blush-set", "Gingham Blush Set", "blush and black", "2830.00", ("File:Casual Fashion 2022 - 51908634741.jpg", "File:Casual Fashion 2022 - 51908634106.jpg", "File:Casual Fashion 2022 - 51909262655.jpg")),
            product("soft-grey-crop-set", "Soft Grey Crop Set", "grey and blush", "2510.00", ("File:Casual Fashion 2022 - 51908724803.jpg", "File:Casual Fashion 2022 - 51908953874.jpg"), availability="limited"),
            product("ivory-blazer-set", "Ivory Blazer Set", "ivory and taupe", "2920.00", ("File:Casual Fashion 2022 - 51908723988.jpg", "File:Casual Fashion 2022 - 51907662707.jpg")),
            product("olive-weekend-set", "Olive Weekend Set", "olive", "2460.00", ("File:Casual Fashion 2022 - 51908630516.jpg", "File:Casual Fashion 2022 - 51908723118.jpg", "File:Casual Fashion 2022 - 51908628886.jpg")),
        ),
    },
)

FASHION_PRODUCTS = tuple({**item, "category_slug": group["slug"], "sizes": group["sizes"]} for group in CATEGORY_GROUPS for item in group["products"])
DEMO_PRODUCT_SLUGS = tuple(item["slug"] for item in FASHION_PRODUCTS)
