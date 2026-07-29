/* ── PreferencesView ────────────────────────────────────────────────

   Explicit + implicit rules + weekly digest.
*/

"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ExplicitPreferences } from "./explicit-preferences";
import { ImplicitPreferences } from "./implicit-preferences";
import { LearningDigest } from "./learning-digest";

export function PreferencesView() {
  return (
    <div className="space-y-4">
      <LearningDigest />
      <Tabs defaultValue="explicit">
        <TabsList>
          <TabsTrigger value="explicit">Explicit Rules</TabsTrigger>
          <TabsTrigger value="implicit">Learned Patterns</TabsTrigger>
        </TabsList>
        <TabsContent value="explicit" className="mt-4">
          <ExplicitPreferences />
        </TabsContent>
        <TabsContent value="implicit" className="mt-4">
          <ImplicitPreferences />
        </TabsContent>
      </Tabs>
    </div>
  );
}
