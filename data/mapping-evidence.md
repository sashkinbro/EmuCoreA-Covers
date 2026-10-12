# Reviewed aliases

The title aliases in `tools/psp_cover_overrides.json` distinguish catalogue naming from serial-list naming; they apply to every serial sharing the verified title.

- Tekken 6 -> IGDB 195868. The bundled IGDB summary explicitly identifies this as the PlayStation Portable port. ID 1247 describes the 2007 arcade release and must not be selected. Validated against ULUS10466 read from the user-owned PSP disc image.
- FIFA 12 / World Class Soccer -> 240392; FIFA 14 Legacy Edition / Edicion Legado -> 240419; Toy Story 3 -> 287629; PES 2014 -> 240467. Matching PSP catalogue entries; validated actual device disc IDs ULES01548, ULES01591, ULUS10507 and ULES01595 respectively.
- Split/Second: Velocity -> 2150. The catalogue has a single PSP platform entry titled `Split/Second`; the redump title uses the European `Velocity` suffix. Validated against ULES01402 read from the user-owned PSP disc image.

# Reviewed serials

Serials absent from the redump source list, confirmed on user-owned PSP hardware.

- ULES01245 (Gran Turismo v2.00, Europe) -> 20426. IGDB 20426 lists only the PlayStation Portable platform.
- ULES00373 (Pirates of the Caribbean: At World's End, Europe) -> 5100.
- ULUS10240 (Prince of Persia: Rival Swords, USA) -> 243129. The IGDB summary for 243129 describes the US version; 243130 is the European version.
- ULES00579 (Prince of Persia: Rival Swords, Europe) -> 243130.
- NPUZ00005 (The Treasures of Montezuma, PSP Mini) -> 44068. ID 44068 is the 2010 PSP/DS release; 327491 is the 2011 PlayStation 3/Vita port.

# Alternative-name matching

Unique normalized equality against IGDB alternative names resolves romanised Japanese titles the redump list uses, for example `Irregular Hunter X` -> Mega Man: Maverick Hunter X, `Yuusha 30` -> Half-Minute Hero or `Minna no Golf Portable` -> Hot Shots Golf: Open Tee. Ambiguous alternative names stay unresolved.

# Romanisation-folded matching

Whole-string equality after canonical romanisation folding (long vowels and Hepburn variants only, no token dropping) resolves titles such as `Kenka Banchou 3: Zenkoku Seiha` -> Kenka Bancho 3, `Naruto Shippuuden: Kizuna Drive` -> Naruto Shippuden: Kizuna Drive or `SD Gundam: GGeneration Portable` -> SD Gundam G Generation Portable. A candidate is accepted only when the folded key is unique. Folded keys must not collapse roman numerals (`VII` stays distinct from `VI`).

# Reviewed title batches

- 30 localised titles carrying market subtitles map through a reviewed alias, for example `Saru! Get You! P!` -> Ape Escape, `M.A.C.H.: Modified Air Combat Heroes` -> Modified Air Combat Heroes, `Pro Cycling Season 2007: Le Tour de France` -> Pro Cycling: Season 2007, `Samurai Dou 2 Portable` -> Way of the Samurai 2.
- 16 duplicate catalogue titles resolve to the canonical entry with the higher IGDB rating count, then the lower IGDB id: Myst -> 236, Full Auto 2: Battlelines -> 7309, Tom Clancy's Rainbow Six: Vegas -> 909, Bomberman Land -> 77674, LEGO Batman: The Videogame -> 2738, LEGO Indiana Jones 2 -> 138, Valkyria Chronicles II -> 14674, Hatsune Miku: Project Diva 2nd -> 11755, Tales of Destiny 2 -> 1203, Pac-Man World Rally -> 2654, Blade Dancer: Lineage of Light -> 23115, Impossible Mission -> 4929, Strike Witches: Hakugin no Tsubasa -> 38449, Namco Museum Vol. 2 -> 20259, Hayarigami 3 -> 61782, Danball Senki -> 72572.

Other unresolved entries remain in review.json. Regional serial support does not imply region-specific box art.
