/** PT53 approved local photography registry. Each URL was verified against the 2026-10-23 media inventory.
 * Physical assets stay in frontend/public/products/media; no media bytes are modified here.
 * This map is explicit: filename inference and approximate matching are forbidden.
 */
export type Photoset = "realistic" | "archetype";
export type TankFinish = "stainless" | "neoprene";
export type TreatmentValve = "clack" | "performance";
export type MediaAsset = { src: string; thumbnail: string };
export type GalleryPhoto = { id: string; label: string; alt: string; media: MediaAsset; fallback?: MediaAsset };
type ConfigMedia = { main: MediaAsset; tank?: MediaAsset; pureline?: MediaAsset };
const PHOTO_REGISTRY: Readonly<Record<string, ConfigMedia>> = {
  "refine:1.5:stainless:clack:realistic": {
    "main": {
      "src": "/products/media/refine/refine_1-5_stainless_clack_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_stainless_clack_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_1p5cf_Stainless_Clack_Realistic_v02.webp",
      "thumbnail": "/products/media/refine/Refine_1p5cf_Stainless_Clack_Realistic_v02_thumb.webp"
    }
  },
  "refine:1.5:stainless:clack:archetype": {
    "main": {
      "src": "/products/media/refine/refine_1-5_stainless_clack_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_stainless_clack_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_1p5cf_Stainless_Clack_Archetype_v02.webp",
      "thumbnail": "/products/media/refine/Refine_1p5cf_Stainless_Clack_Archetype_v02_thumb.webp"
    }
  },
  "refine:1.5:stainless:performance:realistic": {
    "main": {
      "src": "/products/media/refine/refine_1-5_stainless_performance_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_stainless_performance_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_1p5cf_Performance_Realistic_v01.webp",
      "thumbnail": "/products/media/refine/Refine_1p5cf_Performance_Realistic_v01_thumb.webp"
    }
  },
  "refine:1.5:stainless:performance:archetype": {
    "main": {
      "src": "/products/media/refine/refine_1-5_stainless_performance_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_stainless_performance_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_1-5_stainless_performance_archetype.webp",
      "thumbnail": "/products/media/refine/refine_1-5_stainless_performance_archetype_thumb.webp"
    }
  },
  "refine:1.5:neoprene:clack:realistic": {
    "main": {
      "src": "/products/media/refine/refine_1-5_neoprene_clack_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_neoprene_clack_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_1-5_neoprene_clack_realistic.webp",
      "thumbnail": "/products/media/refine/refine_1-5_neoprene_clack_realistic_thumb.webp"
    }
  },
  "refine:1.5:neoprene:clack:archetype": {
    "main": {
      "src": "/products/media/refine/refine_1-5_neoprene_clack_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_neoprene_clack_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_1-5_neoprene_clack_archetype.webp",
      "thumbnail": "/products/media/refine/refine_1-5_neoprene_clack_archetype_thumb.webp"
    }
  },
  "refine:1.5:neoprene:performance:realistic": {
    "main": {
      "src": "/products/media/refine/refine_1-5_neoprene_performance_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_neoprene_performance_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_1-5_neoprene_performance_realistic.webp",
      "thumbnail": "/products/media/refine/refine_1-5_neoprene_performance_realistic_thumb.webp"
    }
  },
  "refine:1.5:neoprene:performance:archetype": {
    "main": {
      "src": "/products/media/refine/refine_1-5_neoprene_performance_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_1-5_neoprene_performance_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_1-5_neoprene_performance_archetype.webp",
      "thumbnail": "/products/media/refine/refine_1-5_neoprene_performance_archetype_thumb.webp"
    }
  },
  "refine:2.0:stainless:clack:realistic": {
    "main": {
      "src": "/products/media/refine/refine_2-0_stainless_clack_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_stainless_clack_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_2cf_Stainless_Clack_Realistic_v02.webp",
      "thumbnail": "/products/media/refine/Refine_2cf_Stainless_Clack_Realistic_v02_thumb.webp"
    }
  },
  "refine:2.0:stainless:clack:archetype": {
    "main": {
      "src": "/products/media/refine/refine_2-0_stainless_clack_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_stainless_clack_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_2cf_Stainless_Clack_Archetype_v02.webp",
      "thumbnail": "/products/media/refine/Refine_2cf_Stainless_Clack_Archetype_v02_thumb.webp"
    }
  },
  "refine:2.0:stainless:performance:realistic": {
    "main": {
      "src": "/products/media/refine/refine_2-0_stainless_performance_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_stainless_performance_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_2cf_Performance_Realistic_v01.webp",
      "thumbnail": "/products/media/refine/Refine_2cf_Performance_Realistic_v01_thumb.webp"
    }
  },
  "refine:2.0:stainless:performance:archetype": {
    "main": {
      "src": "/products/media/refine/refine_2-0_stainless_performance_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_stainless_performance_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/Refine_2cf_Performance_Simplified_v02.webp",
      "thumbnail": "/products/media/refine/Refine_2cf_Performance_Simplified_v02_thumb.webp"
    }
  },
  "refine:2.0:neoprene:clack:realistic": {
    "main": {
      "src": "/products/media/refine/refine_2-0_neoprene_clack_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_neoprene_clack_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_2-0_neoprene_clack_realistic.webp",
      "thumbnail": "/products/media/refine/refine_2-0_neoprene_clack_realistic_thumb.webp"
    }
  },
  "refine:2.0:neoprene:clack:archetype": {
    "main": {
      "src": "/products/media/refine/refine_2-0_neoprene_clack_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_neoprene_clack_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_2-0_neoprene_clack_archetype.webp",
      "thumbnail": "/products/media/refine/refine_2-0_neoprene_clack_archetype_thumb.webp"
    }
  },
  "refine:2.0:neoprene:performance:realistic": {
    "main": {
      "src": "/products/media/refine/refine_2-0_neoprene_performance_realistic_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_neoprene_performance_realistic_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_2-0_neoprene_performance_realistic.webp",
      "thumbnail": "/products/media/refine/refine_2-0_neoprene_performance_realistic_thumb.webp"
    }
  },
  "refine:2.0:neoprene:performance:archetype": {
    "main": {
      "src": "/products/media/refine/refine_2-0_neoprene_performance_archetype_with-brine-tank.webp",
      "thumbnail": "/products/media/refine/thumbnails/refine_2-0_neoprene_performance_archetype_with-brine-tank.webp"
    },
    "tank": {
      "src": "/products/media/refine/refine_2-0_neoprene_performance_archetype.webp",
      "thumbnail": "/products/media/refine/refine_2-0_neoprene_performance_archetype_thumb.webp"
    }
  },
  "essence:1.5:stainless:clack:realistic": {
    "main": {
      "src": "/products/media/essence/essence_1-5_stainless_clack_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_stainless_clack_realistic.webp"
    }
  },
  "essence:1.5:stainless:clack:archetype": {
    "main": {
      "src": "/products/media/essence/essence_1-5_stainless_clack_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_stainless_clack_archetype.webp"
    }
  },
  "essence:1.5:stainless:performance:realistic": {
    "main": {
      "src": "/products/media/essence/essence_1-5_stainless_performance_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_stainless_performance_realistic.webp"
    }
  },
  "essence:1.5:stainless:performance:archetype": {
    "main": {
      "src": "/products/media/essence/essence_1-5_stainless_performance_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_stainless_performance_archetype.webp"
    }
  },
  "essence:1.5:neoprene:clack:realistic": {
    "main": {
      "src": "/products/media/essence/essence_1-5_neoprene_clack_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_neoprene_clack_realistic.webp"
    }
  },
  "essence:1.5:neoprene:clack:archetype": {
    "main": {
      "src": "/products/media/essence/essence_1-5_neoprene_clack_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_neoprene_clack_archetype.webp"
    }
  },
  "essence:1.5:neoprene:performance:realistic": {
    "main": {
      "src": "/products/media/essence/essence_1-5_neoprene_performance_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_neoprene_performance_realistic.webp"
    }
  },
  "essence:1.5:neoprene:performance:archetype": {
    "main": {
      "src": "/products/media/essence/essence_1-5_neoprene_performance_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_1-5_neoprene_performance_archetype.webp"
    }
  },
  "essence:2.0:stainless:clack:realistic": {
    "main": {
      "src": "/products/media/essence/essence_2-0_stainless_clack_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_stainless_clack_realistic.webp"
    }
  },
  "essence:2.0:stainless:clack:archetype": {
    "main": {
      "src": "/products/media/essence/essence_2-0_stainless_clack_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_stainless_clack_archetype.webp"
    }
  },
  "essence:2.0:stainless:performance:realistic": {
    "main": {
      "src": "/products/media/essence/essence_2-0_stainless_performance_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_stainless_performance_realistic.webp"
    }
  },
  "essence:2.0:stainless:performance:archetype": {
    "main": {
      "src": "/products/media/essence/essence_2-0_stainless_performance_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_stainless_performance_archetype.webp"
    }
  },
  "essence:2.0:neoprene:clack:realistic": {
    "main": {
      "src": "/products/media/essence/essence_2-0_neoprene_clack_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_neoprene_clack_realistic.webp"
    }
  },
  "essence:2.0:neoprene:clack:archetype": {
    "main": {
      "src": "/products/media/essence/essence_2-0_neoprene_clack_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_neoprene_clack_archetype.webp"
    }
  },
  "essence:2.0:neoprene:performance:realistic": {
    "main": {
      "src": "/products/media/essence/essence_2-0_neoprene_performance_realistic.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_neoprene_performance_realistic.webp"
    }
  },
  "essence:2.0:neoprene:performance:archetype": {
    "main": {
      "src": "/products/media/essence/essence_2-0_neoprene_performance_archetype.webp",
      "thumbnail": "/products/media/essence/thumbnails/essence_2-0_neoprene_performance_archetype.webp"
    }
  },
  "harmony:1.5:stainless:pass-through:0": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through.webp"
    }
  },
  "harmony:1.5:stainless:pass-through:1": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through_pureline-1.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-1.webp"
    }
  },
  "harmony:1.5:stainless:pass-through:2": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through_pureline-2.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-2.webp"
    }
  },
  "harmony:1.5:stainless:pass-through:3": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through_pureline-3.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-3.webp"
    }
  },
  "harmony:1.5:neoprene:pass-through:0": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through.webp"
    }
  },
  "harmony:1.5:neoprene:pass-through:1": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through_pureline-1.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-1.webp"
    }
  },
  "harmony:1.5:neoprene:pass-through:2": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through_pureline-2.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-2.webp"
    }
  },
  "harmony:1.5:neoprene:pass-through:3": {
    "main": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through_pureline-3.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_1-5_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_1-5_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-3.webp"
    }
  },
  "harmony:2.0:stainless:pass-through:0": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through.webp"
    }
  },
  "harmony:2.0:stainless:pass-through:1": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through_pureline-1.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-1.webp"
    }
  },
  "harmony:2.0:stainless:pass-through:2": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through_pureline-2.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-2.webp"
    }
  },
  "harmony:2.0:stainless:pass-through:3": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through_pureline-3.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_stainless_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_stainless_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-3.webp"
    }
  },
  "harmony:2.0:neoprene:pass-through:0": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through.webp"
    }
  },
  "harmony:2.0:neoprene:pass-through:1": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through_pureline-1.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-1.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-1.webp"
    }
  },
  "harmony:2.0:neoprene:pass-through:2": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through_pureline-2.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-2.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-2.webp"
    }
  },
  "harmony:2.0:neoprene:pass-through:3": {
    "main": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through_pureline-3.webp"
    },
    "tank": {
      "src": "/products/media/harmony/harmony_2-0_neoprene_pass-through.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_2-0_neoprene_pass-through.webp"
    },
    "pureline": {
      "src": "/products/media/harmony/harmony_pureline-3.webp",
      "thumbnail": "/products/media/harmony/thumbnails/harmony_pureline-3.webp"
    }
  }
} as const;
const BRINE_TANK: MediaAsset = {"src": "/products/media/refine/refine_brine-tank.webp", "thumbnail": "/products/media/refine/refine_brine-tank_thumb.webp"} as const;

/** PT53 Origin gallery: restore the previously exposed explicit, per-SKU preview assets.
 * Origin has one approved image collection; when a second photoset does not exist,
 * the same images are displayed for both realistic and archetype.
 * Files are installed into public/products/media/origin by the PT53 restore script.
 */
const ORIGIN_GALLERIES: Readonly<Record<"DD5RO" | "DD6ROAE", GalleryPhoto[]>> = {
  DD5RO: [
    {"id": "system", "label": "Complete five-stage system", "alt": "Origin five-stage complete five-stage system", "media": {"src": "/products/media/origin/DD5RO-hero.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-hero-thumb.webp"}},
    {"id": "filter", "label": "Filter assembly", "alt": "Origin five-stage filter assembly", "media": {"src": "/products/media/origin/DD5RO-filter.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-filter-thumb.webp"}},
    {"id": "storage", "label": "Storage tank", "alt": "Origin five-stage storage tank", "media": {"src": "/products/media/origin/storage-tank.png", "thumbnail": "/products/media/origin/thumbnails/storage-tank-thumb.webp"}},
    {"id": "dimensions", "label": "Illustrative measurement view", "alt": "Origin five-stage illustrative measurement view", "media": {"src": "/products/media/origin/DD5RO-dimensions.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-dimensions-thumb.webp"}},
    {"id": "catalog-dimensions", "label": "Original catalog measurement image", "alt": "Origin five-stage original catalog measurement image", "media": {"src": "/products/media/reverse-osmosis-without-remineralizer-dimensions.webp", "thumbnail": "/products/media/reverse-osmosis-without-remineralizer-dimensions.webp"}},
    {"id": "catalog-spec", "label": "Original specification diagram", "alt": "Origin five-stage original specification diagram", "media": {"src": "/products/media/dd5ro-spec-dimensions.webp", "thumbnail": "/products/media/dd5ro-spec-dimensions.webp"}},
  ],
  DD6ROAE: [
    {"id": "system", "label": "Complete six-stage system", "alt": "Origin six-stage complete six-stage system", "media": {"src": "/products/media/origin/DD6ROAE-hero.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-hero-thumb.webp"}},
    {"id": "filter", "label": "Filter assembly", "alt": "Origin six-stage filter assembly", "media": {"src": "/products/media/origin/DD6ROAE-filter.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-filter-thumb.webp"}},
    {"id": "storage", "label": "Storage tank", "alt": "Origin six-stage storage tank", "media": {"src": "/products/media/origin/storage-tank.png", "thumbnail": "/products/media/origin/thumbnails/storage-tank-thumb.webp"}},
    {"id": "alkaline", "label": "Remineralization stage", "alt": "Origin six-stage remineralization stage", "media": {"src": "/products/media/origin/DD6ROAE-alkaline-detail.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-alkaline-detail-thumb.webp"}},
    {"id": "dimensions", "label": "Illustrative measurement view", "alt": "Origin six-stage illustrative measurement view", "media": {"src": "/products/media/origin/DD6ROAE-dimensions.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-dimensions-thumb.webp"}},
    {"id": "catalog-dimensions", "label": "Original catalog measurement image", "alt": "Origin six-stage original catalog measurement image", "media": {"src": "/products/media/reverse-osmosis-with-remineralizer-dimensions.webp", "thumbnail": "/products/media/reverse-osmosis-with-remineralizer-dimensions.webp"}},
  ],
};

/** Return null for unsupported/unsaleable or invalid configurations, never a guessed photo. */
export function resolveApprovedGallery(
  sku: string, finish: TankFinish = "stainless", valve: TreatmentValve = "clack",
  photoset: Photoset = "realistic", fittingPhoto?: string | null,
  harmonySize: "1.5" | "2.0" = "1.5",
): GalleryPhoto[] | null {
  if (sku === "DD5RO" || sku === "DD6ROAE") return ORIGIN_GALLERIES[sku];
  let family: "refine" | "essence" | "harmony";
  let size: "1.5" | "2.0";
  let pureline = 0;
  if (sku === "DD15SOFT" || sku === "DD20SOFT") {
    family = "refine"; size = sku === "DD15SOFT" ? "1.5" : "2.0";
  } else if (sku === "DD15CATRV" || sku === "DD20CATRV") {
    family = "essence"; size = sku === "DD15CATRV" ? "1.5" : "2.0";
  } else if (sku === "DD15CLEARPTV" || /^DD15CLEARPL[123]$/.test(sku)) {
    family = "harmony"; size = harmonySize; pureline = sku === "DD15CLEARPTV" ? 0 : Number(sku.slice(-1));
  } else return null;
  const key = family === "harmony"
    ? `harmony:${size}:${finish}:pass-through:${pureline}`
    : `${family}:${size}:${finish}:${valve}:${photoset}`;
  // Harmony has no archetype variant: its approved pass-through image stays in place.
  const record = PHOTO_REGISTRY[key];
  if (!record) return null;
  const fallback = family === "harmony" ? record
    : PHOTO_REGISTRY[`${family}:${size}:${finish}:${valve}:realistic`];
  const suffix = `${size} cf ${finish} ${family === "harmony" ? "pass-through" : valve}`;
  const photos: GalleryPhoto[] = [{
    id: "system", label: "Complete system", alt: `${family} ${suffix}, complete configuration`,
    media: record.main, fallback: fallback?.main,
  }];
  if (record.tank) photos.push({ id: "tank", label: "Conditioning tank", alt: `${family} ${suffix}, isolated tank`,
    media: record.tank, fallback: fallback?.tank });
  if (record.pureline) photos.push({ id: "pureline", label: `Pureline ${pureline}-housing assembly`,
    alt: `Standalone Pureline ${pureline}-housing frame, separate from the treatment tank`,
    media: record.pureline, fallback: record.pureline });
  if (family === "refine") photos.push({ id: "brine", label: "Brine tank",
    alt: "Separate Refine brine tank", media: BRINE_TANK });
  if (family !== "harmony" && fittingPhoto) photos.push({ id: "hookup", label: "Selected connection fitting",
    alt: "Individual selected installation fitting", media: {src: fittingPhoto, thumbnail: fittingPhoto} });
  return photos;
}

export function isPhotographyIntegratedSku(sku: string): boolean {
  return resolveApprovedGallery(sku) !== null;
}

/** Deterministic storefront image: same configuration and photoset as the detail default. */
export function approvedLandingPhoto(sku: string, photoset: Photoset): GalleryPhoto | null {
  // Landing-page imagery is unchanged; only the missing detail galleries are restored.
  if (sku === "DD5RO" || sku === "DD6ROAE") return null;
  return resolveApprovedGallery(sku, "stainless", "clack", photoset)?.[0] ?? null;
}
