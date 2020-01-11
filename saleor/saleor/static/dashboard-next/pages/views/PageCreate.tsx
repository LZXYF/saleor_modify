import React from "react";

import { WindowTitle } from "@saleor/components/WindowTitle";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import PageDetailsPage from "../components/PageDetailsPage";
import { TypedPageCreate } from "../mutations";
import { PageCreate as PageCreateData } from "../types/PageCreate";
import { pageListUrl, pageUrl } from "../urls";

export interface PageCreateProps {
  id: string;
}

export const PageCreate: React.StatelessComponent<PageCreateProps> = () => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handlePageCreate = (data: PageCreateData) => {
    if (data.pageCreate.errors.length === 0) {
      notify({
        text: i18n.t("Successfully created new page", {
          context: "notification"
        })
      });
      navigate(pageUrl(data.pageCreate.page.id));
    }
  };

  return (
    <TypedPageCreate onCompleted={handlePageCreate}>
      {(pageCreate, pageCreateOpts) => {
        const formTransitionState = getMutationState(
          pageCreateOpts.called,
          pageCreateOpts.loading,
          maybe(() => pageCreateOpts.data.pageCreate.errors)
        );

        return (
          <>
            <WindowTitle title={i18n.t("Create page")} />
            <PageDetailsPage
              disabled={pageCreateOpts.loading}
              errors={maybe(() => pageCreateOpts.data.pageCreate.errors, [])}
              saveButtonBarState={formTransitionState}
              page={null}
              onBack={() => navigate(pageListUrl())}
              onRemove={() => undefined}
              onSubmit={formData =>
                pageCreate({
                  variables: {
                    input: {
                      contentJson: JSON.stringify(formData.content),
                      isPublished: formData.isPublished
                        ? true
                        : formData.publicationDate === ""
                        ? false
                        : true,
                      publicationDate: formData.isPublished
                        ? null
                        : formData.publicationDate === ""
                        ? null
                        : formData.publicationDate,
                      seo: {
                        description: formData.seoDescription,
                        title: formData.seoTitle
                      },
                      slug: formData.slug === "" ? null : formData.slug,
                      title: formData.title
                    }
                  }
                })
              }
            />
          </>
        );
      }}
    </TypedPageCreate>
  );
};
PageCreate.displayName = "PageCreate";
export default PageCreate;
