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

Other unresolved entries remain in review.json. Regional serial support does not imply region-specific box art.
