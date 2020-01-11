import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import { EditorState, EntityInstance, RichUtils } from "draft-js";
import React from "react";

import i18n from "../../i18n";
import Form from "../Form";

interface LinkSourceProps {
  editorState: EditorState;
  entity?: EntityInstance;
  entityType: {
    type: string;
  };
  onComplete: (updateState: EditorState) => void;
  onClose: () => void;
}

class LinkSource extends React.Component<LinkSourceProps> {
  submit = (url: string) => {
    const { editorState, entityType, onComplete } = this.props;

    if (url) {
      const content = editorState.getCurrentContent();
      const contentWithEntity = content.createEntity(
        entityType.type,
        "MUTABLE",
        { url }
      );
      const entityKey = contentWithEntity.getLastCreatedEntityKey();
      const newEditorState = EditorState.set(editorState, {
        currentContent: contentWithEntity
      });
      const nextState = RichUtils.toggleLink(
        newEditorState,
        newEditorState.getSelection(),
        entityKey
      );

      onComplete(nextState);
    } else {
      onComplete(editorState);
    }
  };

  render() {
    const { entity, onClose } = this.props;
    const initial = entity ? entity.getData().url : "";

    return (
      <Dialog onClose={onClose} open={true} fullWidth maxWidth="sm">
        <Form
          initial={{ url: initial }}
          onSubmit={({ url }) => this.submit(url)}
        >
          {({ data, change, submit }) => (
            <>
              <DialogTitle>{i18n.t("Add or Edit Link")}</DialogTitle>
              <DialogContent>
                <TextField
                  name="url"
                  fullWidth
                  label={i18n.t("URL Linked")}
                  value={data.url}
                  onChange={change}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <Button onClick={submit} color="secondary" variant="contained">
                  {i18n.t("Save", { context: "button" })}
                </Button>
              </DialogActions>
            </>
          )}
        </Form>
      </Dialog>
    );
  }
}
export default LinkSource;
